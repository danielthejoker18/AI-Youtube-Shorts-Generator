"""
Configurações centralizadas do sistema.
"""

import os
from dataclasses import dataclass
from typing import Dict, Any, Optional
from pathlib import Path
from dotenv import load_dotenv

# Carrega variáveis de ambiente
load_dotenv()

@dataclass
class PathConfig:
    """Configurações de caminhos do sistema"""
    
    # Diretórios principais
    BASE_DIR: Path = Path(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
    VIDEOS_DIR: Path = BASE_DIR / "videos"
    RESULTS_DIR: Path = BASE_DIR / "results"
    CACHE_DIR: Path = BASE_DIR / "cache"
    LOGS_DIR: Path = BASE_DIR / "logs"
    
    def __post_init__(self):
        """Garante que os diretórios existem"""
        for path in [self.VIDEOS_DIR, self.RESULTS_DIR, self.CACHE_DIR, self.LOGS_DIR]:
            path.mkdir(parents=True, exist_ok=True)

@dataclass
class APIConfig:
    """Configurações de APIs externas"""
    
    # OpenAI
    OPENAI_API_KEY: Optional[str] = os.getenv("OPENAI_API_KEY")
    OPENAI_MODEL: str = "gpt-3.5-turbo"
    
    # YouTube
    YOUTUBE_API_KEY: Optional[str] = os.getenv("YOUTUBE_API_KEY")
    
    def validate(self) -> Dict[str, bool]:
        """
        Valida as configurações de API.
        
        Returns:
            Dict com status de cada API
        """
        return {
            "openai": bool(self.OPENAI_API_KEY),
            "youtube": bool(self.YOUTUBE_API_KEY)
        }

@dataclass
class ProcessingConfig:
    """Configurações de processamento"""
    
    # Idiomas suportados
    SUPPORTED_LANGUAGES: list[str] = ("en", "pt")
    
    # Limites
    MAX_VIDEO_DURATION: int = 600  # 10 minutos
    MIN_SHORT_DURATION: int = 15
    MAX_SHORT_DURATION: int = 60
    
    # Qualidade
    VIDEO_QUALITY: str = "1080p"
    AUDIO_QUALITY: str = "192k"
    
    # Performance
    USE_GPU: bool = False
    BATCH_SIZE: int = 1

@dataclass
class LogConfig:
    """Configurações de logging"""
    
    LEVEL: str = "INFO"
    FORMAT: str = "%(asctime)s | %(levelname)-8s | %(message)s"
    DATE_FORMAT: str = "%Y-%m-%d %H:%M:%S"
    MAX_BYTES: int = 10 * 1024 * 1024  # 10MB
    BACKUP_COUNT: int = 5

class Config:
    """Configuração global do sistema"""
    
    def __init__(self):
        self.paths = PathConfig()
        self.apis = APIConfig()
        self.processing = ProcessingConfig()
        self.logging = LogConfig()
        
    def validate(self) -> Dict[str, Any]:
        """
        Valida todas as configurações.
        
        Returns:
            Dict com status de cada componente
        """
        status = {
            "paths": all(p.exists() for p in [
                self.paths.VIDEOS_DIR,
                self.paths.RESULTS_DIR,
                self.paths.CACHE_DIR,
                self.paths.LOGS_DIR
            ]),
            "apis": self.apis.validate()
        }
        return status

# Instância global de configuração
config = Config()
