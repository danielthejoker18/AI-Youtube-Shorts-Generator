"""
Language detection for text and audio.
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

# Ensure consistent results
DetectorFactory.seed = 0

logger = ComponentLogger(__name__)

@dataclass
class LanguageConfidence:
    """Confidence of language detection."""
    
    language: str
    confidence: float

class LanguageDetector:
    """
    Detects language in text and audio.
    """
    
    def __init__(self):
        """Initialize the language detector."""
        self.config = config.processing
        self._whisper_model = None
    
    @property
    def whisper_model(self):
        """Load Whisper model on demand."""
        if self._whisper_model is None:
            try:
                self._whisper_model = whisper.load_model("base")
            except Exception as e:
                raise LanguageError(f"Error loading Whisper model: {e}")
        return self._whisper_model
    
    def detect_text(self, text: str) -> LanguageConfidence:
        """
        Detects language in text.
        
        Args:
            text: Text to analyze
            
        Returns:
            LanguageConfidence with detected language
            
        Raises:
            LanguageError: If there is an error in detection
        """
        try:
            # Detect with confidence
            langs = detect_langs(text)
            if not langs:
                raise LanguageError("Unable to detect language")
                
            # Get most likely language
            best_lang = langs[0]
            return LanguageConfidence(
                language=best_lang.lang,
                confidence=best_lang.prob
            )
            
        except Exception as e:
            raise LanguageError(f"Error detecting language: {e}")
    
    def detect_text_multi(self, text: str, min_confidence: float = 0.1) -> List[LanguageConfidence]:
        """
        Detects multiple possible languages in text.
        
        Args:
            text: Text to analyze
            min_confidence: Minimum confidence
            
        Returns:
            List of LanguageConfidence ordered by confidence
            
        Raises:
            LanguageError: If there is an error in detection
        """
        try:
            # Detect all possible languages
            langs = detect_langs(text)
            
            # Filter and convert
            return [
                LanguageConfidence(
                    language=lang.lang,
                    confidence=lang.prob
                )
                for lang in langs
                if lang.prob >= min_confidence
            ]
            
        except Exception as e:
            raise LanguageError(f"Error detecting languages: {e}")
    
    def detect_audio(
        self,
        audio_path: Path,
        sample_duration: float = 30.0
    ) -> LanguageConfidence:
        """
        Detects language in audio.
        
        Args:
            audio_path: Path to audio file
            sample_duration: Sample duration in seconds
            
        Returns:
            LanguageConfidence with detected language
            
        Raises:
            LanguageError: If there is an error in detection
        """
        try:
            # Load audio
            result = self.whisper_model.detect_language(str(audio_path))[0]
            
            return LanguageConfidence(
                language=result["language"],
                confidence=result["confidence"]
            )
            
        except Exception as e:
            raise LanguageError(f"Error detecting language in audio: {e}")
    
    def is_supported(self, language: str) -> bool:
        """
        Checks if a language is supported.
        
        Args:
            language: Language code
            
        Returns:
            True if supported
        """
        return language in self.config.SUPPORTED_LANGUAGES
    
    def validate_language(self, detected: LanguageConfidence) -> Optional[str]:
        """
        Validates a detected language.
        
        Args:
            detected: Detection result
            
        Returns:
            Error message or None if valid
        """
        # Check minimum confidence
        if detected.confidence < 0.5:
            return f"Low confidence in detection ({detected.confidence:.2f})"
        
        # Check if supported
        if not self.is_supported(detected.language):
            return f"Unsupported language: {detected.language}"
        
        return None
