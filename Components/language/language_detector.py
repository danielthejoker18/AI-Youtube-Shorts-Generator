"""
Detecção de idioma em texto e áudio.
"""

from typing import Dict, Optional, List
import numpy as np
from pathlib import Path
from dataclasses import dataclass

from langdetect import detect, detect_langs, DetectorFactory
import whisper

from ..core.logger import ComponentLogger
from ..core.config import config
from ..core.exceptions import LanguageError
from ..media.media_utils import get_audio_features

# Garante resultados consistentes
DetectorFactory.seed = 0

logger = ComponentLogger(__name__)

@dataclass
class LanguageConfidence:
    """Confiança da detecção de idioma."""
    
    language: str
    confidence: float

class LanguageDetector:
    """
    Detecta idioma em texto e áudio.
    """
    
    def __init__(self):
        """Inicializa o detector de idioma."""
        self.config = config.processing
        self._whisper_model = None
    
    @property
    def whisper_model(self):
        """Carrega modelo Whisper sob demanda."""
        if self._whisper_model is None:
            try:
                self._whisper_model = whisper.load_model("base")
            except Exception as e:
                raise LanguageError(f"Erro ao carregar modelo Whisper: {e}")
        return self._whisper_model
    
    def detect_text(self, text: str) -> LanguageConfidence:
        """
        Detecta idioma em texto.
        
        Args:
            text: Texto para análise
            
        Returns:
            LanguageConfidence com idioma detectado
            
        Raises:
            LanguageError: Se houver erro na detecção
        """
        try:
            # Detecta com confiança
            langs = detect_langs(text)
            if not langs:
                raise LanguageError("Não foi possível detectar idioma")
                
            # Pega idioma mais provável
            best_lang = langs[0]
            return LanguageConfidence(
                language=best_lang.lang,
                confidence=best_lang.prob
            )
            
        except Exception as e:
            raise LanguageError(f"Erro ao detectar idioma: {e}")
    
    def detect_text_multi(self, text: str, min_confidence: float = 0.1) -> List[LanguageConfidence]:
        """
        Detecta múltiplos idiomas possíveis em texto.
        
        Args:
            text: Texto para análise
            min_confidence: Confiança mínima
            
        Returns:
            Lista de LanguageConfidence ordenada por confiança
            
        Raises:
            LanguageError: Se houver erro na detecção
        """
        try:
            # Detecta todos os idiomas possíveis
            langs = detect_langs(text)
            
            # Filtra e converte
            return [
                LanguageConfidence(
                    language=lang.lang,
                    confidence=lang.prob
                )
                for lang in langs
                if lang.prob >= min_confidence
            ]
            
        except Exception as e:
            raise LanguageError(f"Erro ao detectar idiomas: {e}")
    
    def detect_audio(
        self,
        audio_path: Path,
        sample_duration: float = 30.0
    ) -> LanguageConfidence:
        """
        Detecta idioma em áudio.
        
        Args:
            audio_path: Caminho do arquivo de áudio
            sample_duration: Duração da amostra em segundos
            
        Returns:
            LanguageConfidence com idioma detectado
            
        Raises:
            LanguageError: Se houver erro na detecção
        """
        try:
            # Carrega áudio
            result = self.whisper_model.detect_language(str(audio_path))[0]
            
            return LanguageConfidence(
                language=result["language"],
                confidence=result["confidence"]
            )
            
        except Exception as e:
            raise LanguageError(f"Erro ao detectar idioma em áudio: {e}")
    
    def is_supported(self, language: str) -> bool:
        """
        Verifica se um idioma é suportado.
        
        Args:
            language: Código do idioma
            
        Returns:
            True se suportado
        """
        return language in self.config.SUPPORTED_LANGUAGES
    
    def validate_language(self, detected: LanguageConfidence) -> Optional[str]:
        """
        Valida um idioma detectado.
        
        Args:
            detected: Resultado da detecção
            
        Returns:
            Mensagem de erro ou None se válido
        """
        # Checa confiança mínima
        if detected.confidence < 0.5:
            return f"Baixa confiança na detecção ({detected.confidence:.2f})"
        
        # Checa se é suportado
        if not self.is_supported(detected.language):
            return f"Idioma não suportado: {detected.language}"
        
        return None
