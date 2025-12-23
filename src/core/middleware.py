"""
Authentication Middleware
JWT token validation and user extraction.
"""
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt

from src.core.config import settings
from src.core.database import get_supabase
from src.core.exceptions import InvalidTokenError


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def get_current_user(token: str = Depends(oauth2_scheme), supabase = Depends(get_supabase)) -> dict:
    """
    Middleware dependency to validate the token and retrieve the current user.
    
    Args:
        token: JWT token from Authorization header
        supabase: Supabase client instance
        
    Returns:
        dict: User data from database
        
    Raises:
        InvalidTokenError: If token is invalid or user not found
    """
    try:
        # Decode JWT token
        payload = jwt.decode(
            token, 
            settings.SECRET_KEY, 
            algorithms=[settings.ALGORITHM]
        )
        email: str = payload.get("sub")
        
        if email is None:
            raise InvalidTokenError()
            
    except JWTError:
        raise InvalidTokenError()
    
    # Query database for user
    response = supabase.table("users_login").select("*").eq("email", email).execute()
    user = response.data[0] if response.data else None
    
    if user is None:
        raise InvalidTokenError()
    
    return user


def get_current_active_user(current_user: dict = Depends(get_current_user)) -> dict:
    """
    Get current active user.
    
    Args:
        current_user: User from get_current_user
        
    Returns:
        dict: Active user data
        
    Raises:
        HTTPException: If user is inactive
    """
    if not current_user.get("is_active", True):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user"
        )
    return current_user


def get_current_user_optional(token: str = Depends(oauth2_scheme), supabase = Depends(get_supabase)) -> dict | None:
    """
    Get current user but don't raise error if not authenticated.
    Returns None instead of raising.
    
    Args:
        token: JWT token from Authorization header
        supabase: Supabase client instance
        
    Returns:
        dict: User data if valid, None otherwise
    """
    try:
        payload = jwt.decode(
            token, 
            settings.SECRET_KEY, 
            algorithms=[settings.ALGORITHM]
        )
        email: str = payload.get("sub")
        
        if email is None:
            return None
            
    except JWTError:
        return None
    
    response = supabase.table("users_login").select("*").eq("email", email).execute()
    user = response.data[0] if response.data else None
    
    return user
