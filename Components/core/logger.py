"""
Sistema centralizado de logging.
"""

import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Optional
from datetime import datetime

from .config import config

class ComponentLogger:
    """
    Logger personalizado para componentes do sistema.
    
    Attributes:
        name: Nome do componente
        logger: Instância do logger
    """
    
    def __init__(self, name: str):
        """
        Inicializa um novo logger para um componente.
        
        Args:
            name: Nome do componente
        """
        self.name = name
        self.logger = self._setup_logger()
    
    def _setup_logger(self) -> logging.Logger:
        """
        Configura o logger com handlers para arquivo e console.
        
        Returns:
            Logger configurado
        """
        logger = logging.getLogger(self.name)
        logger.setLevel(config.logging.LEVEL)
        
        # Evita duplicação de handlers
        if logger.handlers:
            return logger
        
        # Formato comum para todos os handlers
        formatter = logging.Formatter(
            fmt=config.logging.FORMAT,
            datefmt=config.logging.DATE_FORMAT
        )
        
        # Handler para arquivo
        file_handler = self._create_file_handler(formatter)
        if file_handler:
            logger.addHandler(file_handler)
        
        # Handler para console
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
        
        return logger
    
    def _create_file_handler(self, formatter: logging.Formatter) -> Optional[RotatingFileHandler]:
        """
        Cria um handler para arquivo com rotação.
        
        Args:
            formatter: Formatador para as mensagens de log
            
        Returns:
            Handler configurado ou None se houver erro
        """
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{self.name}_{timestamp}.log"
            filepath = Path(config.paths.LOGS_DIR) / filename
            
            handler = RotatingFileHandler(
                filepath,
                maxBytes=config.logging.MAX_BYTES,
                backupCount=config.logging.BACKUP_COUNT
            )
            handler.setFormatter(formatter)
            return handler
        except Exception as e:
            print(f"Erro ao criar file handler: {e}")
            return None
    
    def debug(self, msg: str, *args, **kwargs):
        """Log debug message."""
        self.logger.debug(msg, *args, **kwargs)
    
    def info(self, msg: str, *args, **kwargs):
        """Log info message."""
        self.logger.info(msg, *args, **kwargs)
    
    def warning(self, msg: str, *args, **kwargs):
        """Log warning message."""
        self.logger.warning(msg, *args, **kwargs)
    
    def error(self, msg: str, *args, **kwargs):
        """Log error message."""
        self.logger.error(msg, *args, **kwargs)
    
    def critical(self, msg: str, *args, **kwargs):
        """Log critical message."""
        self.logger.critical(msg, *args, **kwargs)
    
    def exception(self, msg: str, *args, **kwargs):
        """Log exception message."""
        self.logger.exception(msg, *args, **kwargs)
