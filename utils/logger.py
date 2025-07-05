"""
Logging utilities for DMM Logger application.
"""

import logging
import os
from datetime import datetime
from typing import Optional


def setup_logger(name: str = 'dmm_logger', 
                log_file: Optional[str] = None,
                level: int = logging.INFO) -> logging.Logger:
    """
    Set up a logger with file and console handlers.
    
    Args:
        name: Logger name
        log_file: Path to log file (optional)
        level: Logging level
        
    Returns:
        Configured logger instance
    """
    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Clear existing handlers
    logger.handlers.clear()
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File handler (if log_file specified)
    if log_file:
        # Create logs directory if it doesn't exist
        log_dir = os.path.dirname(log_file)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir)
            
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger


def get_default_log_file() -> str:
    """
    Get default log file path.
    
    Returns:
        Default log file path
    """
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    return f"logs/dmm_logger_{timestamp}.log"


class LoggerMixin:
    """
    Mixin class to add logging capabilities to other classes.
    """
    
    def __init__(self, logger_name: Optional[str] = None):
        """
        Initialize logger.
        
        Args:
            logger_name: Name for the logger (defaults to class name)
        """
        if logger_name is None:
            logger_name = self.__class__.__name__
        
        self.logger = setup_logger(logger_name)
    
    def log_info(self, message: str):
        """Log info message."""
        self.logger.info(message)
    
    def log_warning(self, message: str):
        """Log warning message."""
        self.logger.warning(message)
    
    def log_error(self, message: str):
        """Log error message."""
        self.logger.error(message)
    
    def log_debug(self, message: str):
        """Log debug message."""
        self.logger.debug(message)
    
    def log_exception(self, message: str, exc_info: bool = True):
        """Log exception with traceback."""
        self.logger.exception(message, exc_info=exc_info) 