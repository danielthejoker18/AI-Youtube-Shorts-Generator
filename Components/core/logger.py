"""
Logging configuration for the application.
"""

import logging
import os
from pathlib import Path
from typing import Optional

class ComponentLogger:
    """Component-specific logger."""
    
    def __init__(self, name: str, log_dir: Optional[str] = None):
        """
        Initialize logger.
        
        Args:
            name: Logger name
            log_dir: Optional log directory
        """
        self.logger = logging.getLogger(name)
        
        if not self.logger.handlers:
            self.logger.setLevel(logging.INFO)
            
            # Console handler
            console = logging.StreamHandler()
            console.setLevel(logging.INFO)
            console.setFormatter(
                logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            )
            self.logger.addHandler(console)
            
            # File handler if directory specified
            if log_dir:
                os.makedirs(log_dir, exist_ok=True)
                file_path = Path(log_dir) / f"{name}.log"
                file_handler = logging.FileHandler(file_path)
                file_handler.setLevel(logging.DEBUG)
                file_handler.setFormatter(
                    logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
                )
                self.logger.addHandler(file_handler)
    
    def debug(self, msg: str):
        """Log debug message."""
        self.logger.debug(msg)
    
    def info(self, msg: str):
        """Log info message."""
        self.logger.info(msg)
    
    def warning(self, msg: str):
        """Log warning message."""
        self.logger.warning(msg)
    
    def error(self, msg: str):
        """Log error message."""
        self.logger.error(msg)
    
    def critical(self, msg: str):
        """Log critical message."""
        self.logger.critical(msg)
