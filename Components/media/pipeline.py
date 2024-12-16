"""
Pipeline de processamento de vídeo.
"""

import os
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

from ..core.logger import ComponentLogger
from ..core.exceptions import MediaError
from ..language.transcription import Transcriber
from ..language.highlight_detector import HighlightDetector
from .audio_processor import AudioProcessor
from .face_detector import FaceDetector
from .video_editor import VideoEditor, VideoSegment

logger = ComponentLogger(__name__)

@dataclass
class PipelineConfig:
    """Configuração do pipeline."""
    
    # Highlights
    min_highlight_duration: float = 15.0
    max_highlight_duration: float = 60.0
    min_highlight_score: float = 0.7
    max_highlights: int = 5
    
    # Faces
    detect_faces: bool = True
    min_face_confidence: float = 0.5
    
    # Áudio
    clean_audio: bool = True
    normalize_volume: bool = True
    target_db: float = -20
    
    # Vídeo
    add_subtitles: bool = True
    add_transitions: bool = True
    add_zoom: bool = True
    export_width: int = 1080
    export_height: int = 1920
    export_fps: int = 60
    export_bitrate: str = "2M"

class VideoPipeline:
    """
    Pipeline de processamento de vídeo.
    """
    
    def __init__(
        self,
        config: Optional[PipelineConfig] = None,
        output_dir: Optional[str] = None
    ):
        """
        Inicializa pipeline.
        
        Args:
            config: Configuração opcional
            output_dir: Diretório de saída
        """
        self.logger = logger
        self.config = config or PipelineConfig()
        self.output_dir = output_dir or os.getcwd()
        
        # Inicializa componentes
        self.transcriber = Transcriber()
        self.highlight_detector = HighlightDetector()
        self.audio_processor = AudioProcessor()
        self.face_detector = FaceDetector(
            min_confidence=self.config.min_face_confidence
        )
        self.video_editor = VideoEditor()
    
    def process_video(
        self,
        video_path: str,
        output_name: Optional[str] = None
    ) -> str:
        """
        Processa um vídeo.
        
        Args:
            video_path: Caminho do vídeo
            output_name: Nome do arquivo de saída
            
        Returns:
            Caminho do short gerado
            
        Raises:
            MediaError: Se erro no processamento
        """
        try:
            self.logger.info(f"Iniciando processamento: {video_path}")
            
            # Gera nome de saída
            if not output_name:
                basename = os.path.splitext(os.path.basename(video_path))[0]
                output_name = f"{basename}_short.mp4"
            output_path = os.path.join(self.output_dir, output_name)
            
            # Extrai áudio
            self.logger.info("Extraindo áudio...")
            audio_path = self.audio_processor.extract_audio(
                video_path,
                format="wav",
                sample_rate=16000,
                channels=1
            )
            
            # Processa áudio
            if self.config.clean_audio:
                self.logger.info("Limpando áudio...")
                audio_path = self.audio_processor.remove_noise(audio_path)
            
            if self.config.normalize_volume:
                self.logger.info("Normalizando volume...")
                audio_path = self.audio_processor.normalize_volume(
                    audio_path,
                    target_db=self.config.target_db
                )
            
            # Transcreve áudio
            self.logger.info("Transcrevendo áudio...")
            transcript = self.transcriber.transcribe(audio_path)
            
            # Detecta highlights
            self.logger.info("Detectando highlights...")
            highlights = self.highlight_detector.detect_highlights(
                transcript,
                min_duration=self.config.min_highlight_duration,
                max_duration=self.config.max_highlight_duration,
                min_score=self.config.min_highlight_score,
                max_highlights=self.config.max_highlights
            )
            
            # Detecta faces
            face_tracks = []
            if self.config.detect_faces:
                self.logger.info("Detectando faces...")
                for highlight in highlights:
                    tracks = self.face_detector.detect_faces(
                        video_path,
                        save_preview=True
                    )
                    # Filtra tracks do highlight
                    for track in tracks:
                        if (track.start_time <= highlight.end_time and
                            track.end_time >= highlight.start_time):
                            face_tracks.append(track)
            
            # Prepara segmentos
            segments = []
            for i, highlight in enumerate(highlights):
                # Encontra melhor face track
                best_track = None
                if face_tracks:
                    best_track = max(
                        [t for t in face_tracks if t.start_time <= highlight.end_time
                         and t.end_time >= highlight.start_time],
                        key=lambda t: t.avg_confidence,
                        default=None
                    )
                
                segments.append(VideoSegment(
                    start_time=highlight.start_time,
                    end_time=highlight.end_time,
                    video_path=video_path,
                    audio_path=audio_path,
                    face_track=best_track
                ))
            
            # Prepara legendas
            subtitles = None
            if self.config.add_subtitles:
                subtitles = []
                for highlight in highlights:
                    subtitles.append({
                        "text": highlight.text,
                        "start": highlight.start_time,
                        "end": highlight.end_time
                    })
            
            # Cria short
            self.logger.info("Criando short...")
            short_path = self.video_editor.create_short(
                segments,
                output_path,
                subtitles=subtitles,
                transitions=self.config.add_transitions,
                zoom=self.config.add_zoom
            )
            
            # Exporta no formato correto
            self.logger.info("Exportando short...")
            final_path = self.video_editor.export_for_shorts(
                short_path,
                output_path,
                width=self.config.export_width,
                height=self.config.export_height,
                fps=self.config.export_fps,
                bitrate=self.config.export_bitrate
            )
            
            self.logger.info(f"Short gerado: {final_path}")
            return final_path
            
        except Exception as e:
            raise MediaError(f"Erro no pipeline: {e}")
        
        finally:
            # Limpa arquivos temporários
            if 'audio_path' in locals():
                try:
                    os.remove(audio_path)
                except:
                    pass
            if 'short_path' in locals() and short_path != output_path:
                try:
                    os.remove(short_path)
                except:
                    pass
