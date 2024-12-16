"""
Transcrição de áudio para texto.
"""

from pathlib import Path
from typing import List, Optional, Dict, Any
from dataclasses import dataclass
from datetime import datetime, timedelta

import whisper
from youtube_transcript_api import YouTubeTranscriptApi

from ..core.logger import ComponentLogger
from ..core.config import config
from ..core.exceptions import TranscriptionError
from ..storage.cache_manager import CacheManager
from .language_detector import LanguageDetector, LanguageConfidence

logger = ComponentLogger(__name__)

@dataclass
class TranscriptionSegment:
    """Segmento de transcrição."""
    
    text: str
    start: float
    end: float
    confidence: float

@dataclass
class TranscriptionResult:
    """Resultado completo da transcrição."""
    
    segments: List[TranscriptionSegment]
    language: LanguageConfidence
    duration: float
    word_count: int
    source: str

class Transcriber:
    """
    Transcreve áudio para texto.
    """
    
    def __init__(self):
        """Inicializa o transcritor."""
        self.cache = CacheManager()
        self.lang_detector = LanguageDetector()
        self._whisper_model = None
    
    @property
    def whisper_model(self):
        """Carrega modelo Whisper sob demanda."""
        if self._whisper_model is None:
            try:
                self._whisper_model = whisper.load_model("base")
            except Exception as e:
                raise TranscriptionError(f"Erro ao carregar modelo Whisper: {e}")
        return self._whisper_model
    
    def _get_cache_key(self, video_id: str) -> str:
        """
        Gera chave de cache para um vídeo.
        
        Args:
            video_id: ID do vídeo
            
        Returns:
            Chave de cache
        """
        return f"transcription_{video_id}"
    
    def get_cached(
        self,
        video_id: str,
        max_age: Optional[timedelta] = None
    ) -> Optional[TranscriptionResult]:
        """
        Tenta recuperar transcrição do cache.
        
        Args:
            video_id: ID do vídeo
            max_age: Idade máxima do cache
            
        Returns:
            Transcrição ou None se não encontrada/expirada
        """
        key = self._get_cache_key(video_id)
        data = self.cache.get(key, max_age)
        
        if data:
            try:
                return TranscriptionResult(
                    segments=[
                        TranscriptionSegment(**s)
                        for s in data["segments"]
                    ],
                    language=LanguageConfidence(**data["language"]),
                    duration=data["duration"],
                    word_count=data["word_count"],
                    source=data["source"]
                )
            except Exception as e:
                logger.warning(f"Erro ao carregar cache: {e}")
                self.cache.remove(key)
        
        return None
    
    def save_to_cache(self, video_id: str, result: TranscriptionResult):
        """
        Salva transcrição no cache.
        
        Args:
            video_id: ID do vídeo
            result: Resultado da transcrição
        """
        key = self._get_cache_key(video_id)
        data = {
            "segments": [
                {
                    "text": s.text,
                    "start": s.start,
                    "end": s.end,
                    "confidence": s.confidence
                }
                for s in result.segments
            ],
            "language": {
                "language": result.language.language,
                "confidence": result.language.confidence
            },
            "duration": result.duration,
            "word_count": result.word_count,
            "source": result.source
        }
        self.cache.set(key, data)
    
    def transcribe_youtube(self, video_id: str) -> TranscriptionResult:
        """
        Obtém transcrição de um vídeo do YouTube.
        
        Args:
            video_id: ID do vídeo
            
        Returns:
            Resultado da transcrição
            
        Raises:
            TranscriptionError: Se houver erro na transcrição
        """
        try:
            # Tenta cache primeiro
            cached = self.get_cached(video_id)
            if cached:
                logger.info(f"Usando transcrição em cache para {video_id}")
                return cached
            
            # Obtém transcrições disponíveis
            transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
            
            # Tenta transcrição manual primeiro
            try:
                transcript = transcript_list.find_manually_created_transcript()
            except:
                # Se não houver manual, pega gerada
                transcript = transcript_list.find_generated_transcript()
            
            # Converte para nosso formato
            segments = []
            full_text = ""
            
            for item in transcript.fetch():
                segment = TranscriptionSegment(
                    text=item["text"],
                    start=item["start"],
                    end=item["start"] + item["duration"],
                    confidence=1.0 if transcript.is_manually_created else 0.8
                )
                segments.append(segment)
                full_text += item["text"] + " "
            
            # Detecta idioma
            language = self.lang_detector.detect_text(full_text)
            
            result = TranscriptionResult(
                segments=segments,
                language=language,
                duration=segments[-1].end if segments else 0,
                word_count=len(full_text.split()),
                source="youtube_manual" if transcript.is_manually_created
                    else "youtube_generated"
            )
            
            # Salva no cache
            self.save_to_cache(video_id, result)
            
            return result
            
        except Exception as e:
            raise TranscriptionError(f"Erro ao obter transcrição do YouTube: {e}")
    
    def transcribe_audio(self, audio_path: Path) -> TranscriptionResult:
        """
        Transcreve um arquivo de áudio.
        
        Args:
            audio_path: Caminho do arquivo
            
        Returns:
            Resultado da transcrição
            
        Raises:
            TranscriptionError: Se houver erro na transcrição
        """
        try:
            # Transcreve com Whisper
            result = self.whisper_model.transcribe(str(audio_path))
            
            # Converte para nosso formato
            segments = []
            for segment in result["segments"]:
                segments.append(TranscriptionSegment(
                    text=segment["text"],
                    start=segment["start"],
                    end=segment["end"],
                    confidence=segment.get("confidence", 0.8)
                ))
            
            return TranscriptionResult(
                segments=segments,
                language=LanguageConfidence(
                    language=result["language"],
                    confidence=0.9  # Whisper é bem preciso
                ),
                duration=segments[-1].end if segments else 0,
                word_count=len(result["text"].split()),
                source="whisper"
            )
            
        except Exception as e:
            raise TranscriptionError(f"Erro ao transcrever áudio: {e}")
    
    def merge_segments(
        self,
        segments: List[TranscriptionSegment],
        max_duration: float = 60.0
    ) -> List[TranscriptionSegment]:
        """
        Mescla segmentos curtos.
        
        Args:
            segments: Lista de segmentos
            max_duration: Duração máxima após merge
            
        Returns:
            Lista de segmentos mesclados
        """
        if not segments:
            return []
            
        merged = []
        current = segments[0]
        
        for next_seg in segments[1:]:
            # Se juntar não passa do limite
            if next_seg.end - current.start <= max_duration:
                current = TranscriptionSegment(
                    text=f"{current.text} {next_seg.text}",
                    start=current.start,
                    end=next_seg.end,
                    confidence=(current.confidence + next_seg.confidence) / 2
                )
            else:
                merged.append(current)
                current = next_seg
        
        merged.append(current)
        return merged
