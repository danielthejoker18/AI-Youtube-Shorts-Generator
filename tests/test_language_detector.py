import pytest
from Components.language_detector import LanguageDetector

@pytest.fixture
def language_detector():
    return LanguageDetector()

def test_detect_language_english():
    """Testa detecção de idioma inglês"""
    detector = LanguageDetector()
    text = "This is a test sentence in English."
    result = detector.detect_language(text)
    assert result is not None
    assert result['code'] == 'en'
    assert result['name'] == 'English'
    assert result['confidence'] > 0.8

def test_detect_language_portuguese():
    """Testa detecção de idioma português"""
    detector = LanguageDetector()
    text = "Esta é uma frase de teste em português."
    result = detector.detect_language(text)
    assert result is not None
    assert result['code'] == 'pt'
    assert result['name'] == 'Portuguese'
    assert result['confidence'] > 0.8

def test_detect_language_empty():
    """Testa detecção com texto vazio"""
    detector = LanguageDetector()
    result = detector.detect_language("")
    assert result is None

def test_detect_language_invalid():
    """Testa detecção com texto inválido"""
    detector = LanguageDetector()
    result = detector.detect_language("😊 🌟 🎉")
    assert result is None

def test_detect_language_minimum_confidence():
    """Testa detecção com confiança mínima personalizada"""
    detector = LanguageDetector(min_confidence=0.9)
    text = "This is a test sentence in English."
    result = detector.detect_language(text)
    assert result is not None
    assert result['confidence'] > 0.9

def test_detect_language_unsupported():
    """Testa detecção de idioma não suportado"""
    detector = LanguageDetector()
    # Texto em vietnamita
    text = "Đây là một câu tiếng Việt."
    result = detector.detect_language(text)
    assert result is None
