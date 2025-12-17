"""
Authentication Middleware
JWT token validation and user extraction.
"""
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt

from app.core.config import settings
from app.db.supabase_client import get_supabase
from app.models.user_model import TokenData


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
        HTTPException: If token is invalid or user not found
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        # Decode JWT token
        payload = jwt.decode(
            token, 
            settings.SECRET_KEY, 
            algorithms=[settings.ALGORITHM]
        )
        email: str = payload.get("sub")
        
        if email is None:
            raise credentials_exception
            
        token_data = TokenData(email=email)
        
    except JWTError:
        raise credentials_exception
    
    # Query database for user
    response = supabase.table("users_login").select("*").eq("email", token_data.email).execute()
    user = response.data[0] if response.data else None
    
    if user is None:
        raise credentials_exception
    
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


def get_optional_user(token: str = Depends(oauth2_scheme)) -> dict | None:
    """
    Optionally get current user (doesn't raise exception if not authenticated).
    
    Args:
        token: JWT token from Authorization header
        
    Returns:
        dict | None: User data or None
    """
    try:
        return get_current_user(token)
    except HTTPException:
        return None
