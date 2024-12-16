"""
Processamento principal de vídeo.
"""

from pathlib import Path
from typing import List, Optional, Tuple
from dataclasses import dataclass

from moviepy.editor import VideoFileClip, concatenate_videoclips
import numpy as np

from ..core.logger import ComponentLogger
from ..core.config import config
from ..core.exceptions import VideoProcessingError
from .media_utils import VideoMetadata, get_video_metadata, cleanup_temp_files

logger = ComponentLogger(__name__)

@dataclass
class VideoSegment:
    """Segmento de vídeo para processamento."""
    
    start_time: float
    end_time: float
    transcript: str
    confidence: float

class VideoProcessor:
    """
    Processa vídeos para criar shorts.
    """
    
    def __init__(self):
        """Inicializa o processador de vídeo."""
        self.config = config.processing
    
    def create_short(
        self,
        video_path: Path,
        segments: List[VideoSegment],
        output_path: Optional[Path] = None
    ) -> Path:
        """
        Cria um short a partir de segmentos de vídeo.
        
        Args:
            video_path: Caminho para o vídeo original
            segments: Lista de segmentos para incluir
            output_path: Caminho para salvar o resultado
            
        Returns:
            Path do short criado
            
        Raises:
            VideoProcessingError: Se houver erro no processamento
        """
        try:
            # Valida duração total
            total_duration = sum(s.end_time - s.start_time for s in segments)
            if not self.config.MIN_SHORT_DURATION <= total_duration <= self.config.MAX_SHORT_DURATION:
                raise VideoProcessingError(
                    f"Duração total ({total_duration:.1f}s) fora dos limites "
                    f"({self.config.MIN_SHORT_DURATION}-{self.config.MAX_SHORT_DURATION}s)"
                )
            
            # Cria clips para cada segmento
            with VideoFileClip(str(video_path)) as video:
                clips = []
                for segment in segments:
                    clip = video.subclip(segment.start_time, segment.end_time)
                    clips.append(clip)
                
                # Concatena clips
                final_clip = concatenate_videoclips(clips)
                
                # Define caminho de saída
                if output_path is None:
                    output_path = (
                        config.paths.RESULTS_DIR / 
                        f"{video_path.stem}_short_{len(segments)}_{int(total_duration)}s.mp4"
                    )
                
                # Salva resultado
                final_clip.write_videofile(
                    str(output_path),
                    codec="libx264",
                    audio_codec="aac"
                )
                
            return output_path
            
        except Exception as e:
            raise VideoProcessingError(f"Erro ao criar short: {e}")
        finally:
            cleanup_temp_files(config.paths.RESULTS_DIR)
    
    def extract_faces(
        self,
        video_path: Path,
        timestamp: float,
        min_confidence: float = 0.5
    ) -> List[Tuple[np.ndarray, float]]:
        """
        Extrai faces de um frame específico.
        
        Args:
            video_path: Caminho para o vídeo
            timestamp: Momento do vídeo em segundos
            min_confidence: Confiança mínima para detecção
            
        Returns:
            Lista de tuplas (face_image, confidence)
            
        Raises:
            VideoProcessingError: Se houver erro na detecção
        """
        try:
            # Importa aqui para não depender sempre
            import face_recognition
            from .media_utils import extract_frame
            
            # Extrai frame
            frame = extract_frame(video_path, timestamp)
            
            # Detecta faces
            face_locations = face_recognition.face_locations(frame)
            if not face_locations:
                return []
            
            # Extrai faces e confiança
            faces = []
            for top, right, bottom, left in face_locations:
                face = frame[top:bottom, left:right]
                # Usa tamanho relativo como proxy de confiança
                area = (bottom - top) * (right - left)
                frame_area = frame.shape[0] * frame.shape[1]
                confidence = min(area / frame_area * 4, 1.0)  # Normaliza para [0,1]
                
                if confidence >= min_confidence:
                    faces.append((face, confidence))
            
            return faces
            
        except Exception as e:
            raise VideoProcessingError(f"Erro ao extrair faces: {e}")
    
    @staticmethod
    def validate_video(video_path: Path) -> Tuple[bool, Optional[str]]:
        """
        Valida se um vídeo pode ser processado.
        
        Args:
            video_path: Caminho para o vídeo
            
        Returns:
            Tuple (is_valid, error_message)
        """
        try:
            metadata = get_video_metadata(video_path)
            
            # Checa duração
            if metadata.duration > config.processing.MAX_VIDEO_DURATION:
                return False, f"Vídeo muito longo ({metadata.duration:.1f}s)"
            
            # Checa áudio
            if not metadata.has_audio:
                return False, "Vídeo não possui áudio"
            
            # Checa resolução mínima
            if metadata.height < 720:
                return False, f"Resolução muito baixa ({metadata.width}x{metadata.height})"
            
            return True, None
            
        except Exception as e:
            return False, str(e)
