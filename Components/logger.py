import logging
from logging.handlers import RotatingFileHandler
import os
from datetime import datetime
import sys
from typing import Optional
from pathlib import Path

def setup_logger(name: str, log_file: Optional[str] = None) -> logging.Logger:
    """
    Setup logger with detailed formatting and both file and console output.
    
    Args:
        name: Logger name (usually __name__)
        log_file: Optional specific log file path
        
    Returns:
        logging.Logger: Configured logger instance
    """
    # Create logs directory if it doesn't exist
    os.makedirs('logs', exist_ok=True)

    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    
    # Remove existing handlers to avoid duplicates
    logger.handlers = []

    # Create formatters
    detailed_formatter = logging.Formatter(
        '%(asctime)s | %(levelname)-8s | %(name)s:%(lineno)d | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    console_formatter = logging.Formatter(
        '%(asctime)s | %(levelname)-8s | %(message)s',
        datefmt='%H:%M:%S'
    )

    # File handler (detailed logging)
    if not log_file:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        log_file = os.path.join('logs', f'{name}_{timestamp}.log')
    
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5,
        encoding='utf-8'
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(detailed_formatter)
    logger.addHandler(file_handler)

    # Console handler (info+ only)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)

    return logger

def get_logger(name: str) -> logging.Logger:
    """
    Configura e retorna um logger.
    
    Args:
        name: Nome do logger
        
    Returns:
        Logger configurado
    """
    # Cria diretório de logs se não existir
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    # Configura nome do arquivo de log
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = log_dir / f"{name.replace('.', '_')}_{timestamp}.log"
    
    # Configura o logger
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    
    # Remove handlers existentes
    logger.handlers = []
    
    # Handler para arquivo
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)
    
    # Handler para console
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    
    # Formato do log
    formatter = logging.Formatter('%(asctime)s | %(levelname)-8s | %(name)s:%(lineno)d | %(message)s', 
                                datefmt='%Y-%m-%d %H:%M:%S')
    
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger

def log_section(logger: logging.Logger, title: str) -> None:
    """
    Log a section header to make logs more readable.
    
    Args:
        logger: Logger instance
        title: Section title
    """
    border = "=" * 50
    logger.info(f"\n{border}")
    logger.info(f"=== {title} ===")
    logger.info(f"{border}\n")

# Example usage:
# logger = setup_logger(__name__)
# logger.debug("Debug message")
# logger.info("Info message")
# logger.warning("Warning message")
# logger.error("Error message")
# logger.critical("Critical message")
# log_section(logger, "Section 1")
