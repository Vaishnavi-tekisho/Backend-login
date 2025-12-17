"""
User Models
Pydantic models for user-related API requests and responses.
"""
from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime
from uuid import UUID


# ==================== BASE MODELS ====================

class UserBase(BaseModel):
    """Base user model with common fields."""
    email: EmailStr
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone_number: Optional[str] = None
    location: Optional[str] = None


# ==================== REQUEST MODELS ====================

class UserCreate(UserBase):
    """Request model for user registration."""
    password: str = Field(..., min_length=8)


class UserLogin(BaseModel):
    """Request model for user login."""
    email: EmailStr
    password: str


class UserCreateGoogle(UserBase):
    """Request model for Google OAuth user creation."""
    password: Optional[str] = None
    oauth_provider: str = "google"
    profile_image_url: Optional[str] = None
    oauth_id: Optional[str] = None


class GoogleTokenRequest(BaseModel):
    """Request model for Google token verification."""
    token: str


class UserUpdate(BaseModel):
    """Request model for updating user profile."""
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone_number: Optional[str] = None
    location: Optional[str] = None
    profile_image_url: Optional[str] = None


# ==================== RESPONSE MODELS ====================

class UserResponse(UserBase):
    """Response model for user data."""
    id: int
    profile_image_url: Optional[str] = None
    acc_created_at: Optional[datetime] = None
    is_active: Optional[bool] = True
    email_verified: Optional[bool] = False
    oauth_provider: Optional[str] = None
    
    class Config:
        from_attributes = True


class Token(BaseModel):
    """JWT token response."""
    access_token: str
    token_type: str


class TokenData(BaseModel):
    """Decoded token data."""
    email: Optional[str] = None
    user_id: Optional[UUID] = None


class AuthResponse(BaseModel):
    """Authentication response with token and user data."""
    access_token: str
    token_type: str
    user: UserResponse
