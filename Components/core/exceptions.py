"""
Exceções personalizadas do sistema.
"""

class ComponentError(Exception):
    """Base exception for all component errors."""
    pass

class ConfigError(ComponentError):
    """Erro de configuração."""
    pass

class APIError(ComponentError):
    """Erro em chamadas de API."""
    pass

class MediaError(ComponentError):
    """Erro em processamento de mídia."""
    pass

class TranscriptionError(ComponentError):
    """Erro durante a transcrição."""
    pass

class LanguageError(ComponentError):
    """Erro relacionado a processamento de linguagem."""
    pass

class DownloadError(ComponentError):
    """Erro durante o download."""
    pass

class ProcessingError(ComponentError):
    """Erro durante o processamento de vídeo/áudio."""
    pass

class CacheError(ComponentError):
    """Erro relacionado ao cache."""
    pass

class ValidationError(ComponentError):
    """Erro de validação."""
    pass
