"""Custom exceptions for the project."""

class VideoManagerError(Exception):
    """Raised when there is an error in video management."""
    pass

class TranscriptionError(Exception):
    """Raised when there is an error in video transcription."""
    pass

class ProcessingError(Exception):
    """Raised when there is an error in video processing."""
    pass

class DownloadError(Exception):
    """Raised when there is an error downloading a video."""
    pass

class LanguageError(Exception):
    """Raised when there is an error with language detection or processing."""
    pass

class ConfigurationError(Exception):
    """Raised when there is an error in configuration."""
    pass
