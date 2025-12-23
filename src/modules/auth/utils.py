"""
Auth Utilities
Helper functions specific to authentication module.
"""
import re
from passlib.context import CryptContext


# Password hashing context using bcrypt
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """
    Hash a password using bcrypt.
    
    Args:
        password: Plain text password
        
    Returns:
        str: Hashed password
    """
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plain password against a hashed password.
    
    Args:
        plain_password: Plain text password
        hashed_password: Hashed password
        
    Returns:
        bool: True if match, False otherwise
    """
    return pwd_context.verify(plain_password, hashed_password)


def validate_password_strength(password: str) -> dict:
    """
    Validate password strength.
    
    Requirements:
    - Minimum 8 characters
    - At least one uppercase letter
    - At least one lowercase letter
    - At least one digit
    - At least one special character
    
    Args:
        password: Password to validate
        
    Returns:
        dict: {
            "is_valid": bool,
            "errors": list of error messages,
            "strength": "weak" | "medium" | "strong"
        }
    """
    errors = []
    
    if len(password) < 8:
        errors.append("Password must be at least 8 characters long")
    
    if not re.search(r"[A-Z]", password):
        errors.append("Password must contain at least one uppercase letter")
    
    if not re.search(r"[a-z]", password):
        errors.append("Password must contain at least one lowercase letter")
    
    if not re.search(r"\d", password):
        errors.append("Password must contain at least one digit")
    
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
        errors.append("Password must contain at least one special character")
    
    # Calculate strength
    strength_score = 0
    if len(password) >= 8:
        strength_score += 1
    if len(password) >= 12:
        strength_score += 1
    if re.search(r"[A-Z]", password):
        strength_score += 1
    if re.search(r"[a-z]", password):
        strength_score += 1
    if re.search(r"\d", password):
        strength_score += 1
    if re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
        strength_score += 1
    
    if strength_score <= 2:
        strength = "weak"
    elif strength_score <= 4:
        strength = "medium"
    else:
        strength = "strong"
    
    return {
        "is_valid": len(errors) == 0,
        "errors": errors,
        "strength": strength
    }


def hash_otp(otp: str) -> str:
    """Hash OTP using bcrypt."""
    return pwd_context.hash(otp)


def verify_otp(plain_otp: str, hashed_otp: str) -> bool:
    """Verify OTP against hash."""
    return pwd_context.verify(plain_otp, hashed_otp)
