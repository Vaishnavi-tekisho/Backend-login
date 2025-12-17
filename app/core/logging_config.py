"""
Logging Configuration
Centralized logging setup for the application.
"""
import logging
import sys
from datetime import datetime


def setup_logging(log_level: str = "INFO") -> logging.Logger:
    """
    Configure application-wide logging.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        
    Returns:
        Logger: Configured logger instance
    """
    # Create logger
    logger = logging.getLogger("leadq")
    logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))
    
    # Prevent duplicate handlers
    if logger.handlers:
        return logger
    
    # Console handler with formatting
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG)
    
    # Formatter
    formatter = logging.Formatter(
        fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_handler.setFormatter(formatter)
    
    # Add handler to logger
    logger.addHandler(console_handler)
    
    return logger


# Default logger instance
logger = setup_logging()


def log_request(method: str, path: str, status_code: int, duration_ms: float):
    """Log HTTP request details."""
    logger.info(f"{method} {path} - {status_code} - {duration_ms:.2f}ms")


def log_error(error_type: str, message: str, details: dict = None):
    """Log error with optional details."""
    log_message = f"{error_type}: {message}"
    if details:
        log_message += f" | Details: {details}"
    logger.error(log_message)


def log_auth_event(event: str, email: str, success: bool):
    """Log authentication events."""
    status = "SUCCESS" if success else "FAILED"
    logger.info(f"AUTH [{status}] - {event} - {email}")
