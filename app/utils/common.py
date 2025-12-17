"""
Common Utilities
Shared helper functions used across the application.
"""
import re
from datetime import datetime
from typing import Optional


def is_valid_email(email: str) -> bool:
    """
    Validate email format.
    
    Args:
        email: Email address to validate
        
    Returns:
        bool: True if valid email format
    """
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def is_valid_phone(phone: str) -> bool:
    """
    Validate phone number format (E.164).
    
    Args:
        phone: Phone number to validate
        
    Returns:
        bool: True if valid E.164 format
    """
    pattern = r'^\+\d{10,15}$'
    return bool(re.match(pattern, phone))


def format_datetime(dt: datetime, format_str: str = "%Y-%m-%d %H:%M:%S") -> str:
    """
    Format datetime to string.
    
    Args:
        dt: Datetime object
        format_str: Format string
        
    Returns:
        str: Formatted datetime string
    """
    return dt.strftime(format_str)


def parse_datetime(dt_str: str) -> Optional[datetime]:
    """
    Parse datetime string to datetime object.
    
    Args:
        dt_str: Datetime string (ISO format)
        
    Returns:
        datetime: Parsed datetime or None
    """
    try:
        # Handle different ISO formats
        dt_str_clean = dt_str.replace('Z', '+00:00')
        return datetime.fromisoformat(dt_str_clean)
    except (ValueError, AttributeError):
        return None


def sanitize_string(value: str) -> str:
    """
    Sanitize string input.
    
    Args:
        value: String to sanitize
        
    Returns:
        str: Sanitized string
    """
    if not value:
        return ""
    
    # Remove leading/trailing whitespace
    value = value.strip()
    
    # Remove null bytes
    value = value.replace('\x00', '')
    
    return value


def mask_email(email: str) -> str:
    """
    Mask email for display (privacy).
    
    Example: john.doe@example.com -> j***e@example.com
    
    Args:
        email: Email to mask
        
    Returns:
        str: Masked email
    """
    if not email or '@' not in email:
        return email
    
    local, domain = email.split('@')
    
    if len(local) <= 2:
        masked_local = local[0] + '*'
    else:
        masked_local = local[0] + '*' * (len(local) - 2) + local[-1]
    
    return f"{masked_local}@{domain}"


def mask_phone(phone: str) -> str:
    """
    Mask phone number for display (privacy).
    
    Example: +1234567890 -> +1****7890
    
    Args:
        phone: Phone to mask
        
    Returns:
        str: Masked phone
    """
    if not phone or len(phone) < 8:
        return phone
    
    return phone[:2] + '*' * (len(phone) - 6) + phone[-4:]
