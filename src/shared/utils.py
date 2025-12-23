"""
Common Utilities
Shared utility functions across modules.
"""
import re
from datetime import datetime


def validate_email_format(email: str) -> bool:
    """
    Validate email format using regex.
    
    Args:
        email: Email string to validate
        
    Returns:
        bool: True if valid email format
    """
    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    return re.match(pattern, email) is not None


def validate_phone_number(phone: str) -> bool:
    """
    Validate phone number in E.164 format.
    
    Args:
        phone: Phone number string (should be in E.164 format: +1234567890)
        
    Returns:
        bool: True if valid E.164 format
    """
    pattern = r"^\+\d{10,15}$"
    return re.match(pattern, phone) is not None


def format_datetime(dt: datetime, fmt: str = "%Y-%m-%d %H:%M:%S") -> str:
    """
    Format datetime object to string.
    
    Args:
        dt: Datetime object
        fmt: Format string
        
    Returns:
        str: Formatted datetime string
    """
    if dt is None:
        return None
    return dt.strftime(fmt)


def parse_iso_datetime(iso_string: str) -> datetime:
    """
    Parse ISO datetime string.
    
    Args:
        iso_string: ISO format datetime string
        
    Returns:
        datetime: Parsed datetime object
    """
    try:
        return datetime.fromisoformat(iso_string.replace("Z", "+00:00"))
    except (ValueError, AttributeError):
        return None


def sanitize_string(text: str) -> str:
    """
    Sanitize string input by removing dangerous characters.
    
    Args:
        text: Text to sanitize
        
    Returns:
        str: Sanitized text
    """
    if not text:
        return ""
    # Remove leading/trailing whitespace
    text = text.strip()
    # Remove multiple spaces
    text = re.sub(r"\s+", " ", text)
    return text
