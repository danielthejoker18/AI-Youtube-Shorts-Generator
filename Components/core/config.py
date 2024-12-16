"""
Configuration management for the application.
"""

import os
from pathlib import Path
from typing import Optional, Dict, Any
from dataclasses import dataclass, field
import json

from .exceptions import ConfigError
from .logger import ComponentLogger

logger = ComponentLogger(__name__)

@dataclass
class LLMConfig:
    """LLM provider configuration."""
    
    PROVIDER: str = "openai"
    API_KEY: Optional[str] = None
    MODEL: str = "gpt-4-turbo-preview"
    MAX_TOKENS: int = 4000
    TEMPERATURE: float = 0.7

@dataclass
class ProcessingConfig:
    """Video and audio processing configuration."""
    
    SUPPORTED_LANGUAGES: list = field(default_factory=lambda: ["en", "pt"])
    MAX_VIDEO_LENGTH: int = 60
    MIN_VIDEO_LENGTH: int = 15
    TARGET_FPS: int = 30
    TARGET_WIDTH: int = 1080
    TARGET_HEIGHT: int = 1920
    AUDIO_SAMPLE_RATE: int = 44100

@dataclass
class PathsConfig:
    """File paths configuration."""
    
    BASE_DIR: Path = Path(__file__).parent.parent.parent
    CACHE_DIR: Path = BASE_DIR / "cache"
    TEMP_DIR: Path = BASE_DIR / "temp"
    OUTPUT_DIR: Path = BASE_DIR / "output"
    LOGS_DIR: Path = BASE_DIR / "logs"

@dataclass
class Config:
    """Main application configuration."""
    
    llm: LLMConfig = field(default_factory=LLMConfig)
    processing: ProcessingConfig = field(default_factory=ProcessingConfig)
    paths: PathsConfig = field(default_factory=PathsConfig)
    
    def __post_init__(self):
        """Create required directories."""
        for path in [
            self.paths.CACHE_DIR,
            self.paths.TEMP_DIR,
            self.paths.OUTPUT_DIR,
            self.paths.LOGS_DIR
        ]:
            path.mkdir(parents=True, exist_ok=True)
    
    def load_env(self):
        """Load configuration from environment variables."""
        try:
            # LLM config
            if provider := os.getenv("LLM_PROVIDER"):
                self.llm.PROVIDER = provider
            if api_key := os.getenv("OPENAI_API_KEY"):
                self.llm.API_KEY = api_key
            if model := os.getenv("LLM_MODEL"):
                self.llm.MODEL = model
            
            # Processing config
            if max_length := os.getenv("MAX_VIDEO_LENGTH"):
                self.processing.MAX_VIDEO_LENGTH = int(max_length)
            if min_length := os.getenv("MIN_VIDEO_LENGTH"):
                self.processing.MIN_VIDEO_LENGTH = int(min_length)
            
            logger.info("Environment configuration loaded")
            
        except Exception as e:
            raise ConfigError(f"Error loading environment configuration: {e}")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary."""
        return {
            "llm": {
                "provider": self.llm.PROVIDER,
                "model": self.llm.MODEL,
                "max_tokens": self.llm.MAX_TOKENS,
                "temperature": self.llm.TEMPERATURE
            },
            "processing": {
                "supported_languages": self.processing.SUPPORTED_LANGUAGES,
                "max_video_length": self.processing.MAX_VIDEO_LENGTH,
                "min_video_length": self.processing.MIN_VIDEO_LENGTH,
                "target_fps": self.processing.TARGET_FPS,
                "target_width": self.processing.TARGET_WIDTH,
                "target_height": self.processing.TARGET_HEIGHT,
                "audio_sample_rate": self.processing.AUDIO_SAMPLE_RATE
            },
            "paths": {
                "base_dir": str(self.paths.BASE_DIR),
                "cache_dir": str(self.paths.CACHE_DIR),
                "temp_dir": str(self.paths.TEMP_DIR),
                "output_dir": str(self.paths.OUTPUT_DIR),
                "logs_dir": str(self.paths.LOGS_DIR)
            }
        }
    
    def save(self, path: str):
        """Save configuration to file."""
        try:
            with open(path, "w") as f:
                json.dump(self.to_dict(), f, indent=4)
            logger.info(f"Configuration saved to {path}")
        except Exception as e:
            raise ConfigError(f"Error saving configuration: {e}")
    
    @classmethod
    def load(cls, path: str) -> "Config":
        """Load configuration from file."""
        try:
            with open(path) as f:
                data = json.load(f)
            
            config = cls()
            
            # LLM config
            config.llm.PROVIDER = data["llm"]["provider"]
            config.llm.MODEL = data["llm"]["model"]
            config.llm.MAX_TOKENS = data["llm"]["max_tokens"]
            config.llm.TEMPERATURE = data["llm"]["temperature"]
            
            # Processing config
            config.processing.SUPPORTED_LANGUAGES = data["processing"]["supported_languages"]
            config.processing.MAX_VIDEO_LENGTH = data["processing"]["max_video_length"]
            config.processing.MIN_VIDEO_LENGTH = data["processing"]["min_video_length"]
            config.processing.TARGET_FPS = data["processing"]["target_fps"]
            config.processing.TARGET_WIDTH = data["processing"]["target_width"]
            config.processing.TARGET_HEIGHT = data["processing"]["target_height"]
            config.processing.AUDIO_SAMPLE_RATE = data["processing"]["audio_sample_rate"]
            
            logger.info(f"Configuration loaded from {path}")
            return config
            
        except Exception as e:
            raise ConfigError(f"Error loading configuration: {e}")

# Global configuration instance
config = Config()
