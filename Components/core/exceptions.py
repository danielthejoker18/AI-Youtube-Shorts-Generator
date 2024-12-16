"""
Custom exceptions for the application.
"""

class BaseError(Exception):
    """Base exception class."""
    pass

class ConfigError(BaseError):
    """Configuration error."""
    pass

class MediaError(BaseError):
    """Media processing error."""
    pass

class LanguageError(BaseError):
    """Language processing error."""
    pass

class LLMError(BaseError):
    """LLM API error."""
    pass

class VideoError(BaseError):
    """Video processing error."""
    pass

class AudioError(BaseError):
    """Audio processing error."""
    pass

class ValidationError(BaseError):
    """Data validation error."""
    pass
