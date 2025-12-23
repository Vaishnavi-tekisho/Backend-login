"""
Application Logging Configuration
Centralized logging setup.
"""
import logging
import sys
from logging.handlers import RotatingFileHandler


def setup_logging(log_file: str = "app.log", level: int = logging.INFO) -> None:
    """
    Configure application-wide logging.
    
    Args:
        log_file: Path to log file
        level: Logging level (default: INFO)
    """
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    
    # File handler with rotation
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=10485760,  # 10MB
        backupCount=5
    )
    file_handler.setFormatter(formatter)
    
    # Root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)


# Get logger for a module
def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance for a module.
    
    Args:
        name: Module name
        
    Returns:
        logging.Logger: Logger instance
    """
    return logging.getLogger(name)
