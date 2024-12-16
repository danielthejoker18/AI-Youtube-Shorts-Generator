from typing import Dict, Optional
from langdetect import detect, detect_langs
from langdetect.lang_detect_exception import LangDetectException
from .logger import get_logger

logger = get_logger(__name__)

class LanguageDetector:
    """Classe para detectar o idioma do texto e verificar a confiança da detecção"""
    
    SUPPORTED_LANGUAGES = {
        'en': 'English',
        'pt': 'Portuguese',
        'es': 'Spanish',
        'fr': 'French',
        'de': 'German',
        'it': 'Italian',
        'nl': 'Dutch',
        'pl': 'Polish',
        'ru': 'Russian',
        'ja': 'Japanese',
        'ko': 'Korean',
        'zh-cn': 'Chinese (Simplified)',
        'zh-tw': 'Chinese (Traditional)',
        'ar': 'Arabic',
        'hi': 'Hindi',
        'tr': 'Turkish'
    }
    
    def __init__(self, min_confidence: float = 0.8):
        """
        Inicializa o detector de idioma.
        
        Args:
            min_confidence: Confiança mínima para aceitar a detecção (0.0 a 1.0)
        """
        self.min_confidence = min_confidence
        
    def detect_language(self, text: str) -> Optional[Dict[str, str]]:
        """
        Detecta o idioma do texto e retorna informações sobre a detecção.
        
        Args:
            text: Texto para detectar o idioma
            
        Returns:
            Dict com informações do idioma detectado ou None se falhar:
            {
                'code': código do idioma (ex: 'en', 'pt'),
                'name': nome do idioma em inglês,
                'confidence': confiança da detecção (0.0 a 1.0)
            }
        """
        try:
            # Detecta todos os idiomas possíveis com confiança
            langs = detect_langs(text)
            
            if not langs:
                logger.warning("No language detected")
                return None
                
            # Pega o idioma com maior confiança
            best_match = langs[0]
            confidence = best_match.prob
            lang_code = best_match.lang
            
            # Verifica se atinge a confiança mínima
            if confidence < self.min_confidence:
                logger.warning(f"Language detection confidence too low: {confidence:.2f}")
                return None
                
            # Verifica se é um idioma suportado
            if lang_code not in self.SUPPORTED_LANGUAGES:
                logger.warning(f"Unsupported language detected: {lang_code}")
                return None
                
            return {
                'code': lang_code,
                'name': self.SUPPORTED_LANGUAGES[lang_code],
                'confidence': confidence
            }
            
        except LangDetectException as e:
            logger.error(f"Language detection failed: {e}")
            return None
            
    def is_language(self, text: str, lang_code: str, min_confidence: Optional[float] = None) -> bool:
        """
        Verifica se o texto está em um idioma específico.
        
        Args:
            text: Texto para verificar
            lang_code: Código do idioma para verificar (ex: 'en', 'pt')
            min_confidence: Confiança mínima opcional (sobrescreve o valor padrão)
            
        Returns:
            bool: True se o texto está no idioma especificado com a confiança mínima
        """
        result = self.detect_language(text)
        if not result:
            return False
            
        # Usa a confiança mínima especificada ou o valor padrão
        threshold = min_confidence if min_confidence is not None else self.min_confidence
        
        return (
            result['code'] == lang_code and
            result['confidence'] >= threshold
        )
        
    def is_english(self, text: str, min_confidence: Optional[float] = None) -> bool:
        """Verifica se o texto está em inglês"""
        return self.is_language(text, 'en', min_confidence)
        
    def is_portuguese(self, text: str, min_confidence: Optional[float] = None) -> bool:
        """Verifica se o texto está em português"""
        return self.is_language(text, 'pt', min_confidence)
