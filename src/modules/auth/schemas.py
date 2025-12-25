"""
Auth Schemas
Pydantic models for auth-related API requests and responses.
"""
from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime
from uuid import UUID


# ==================== USER LOGIN/PROFILE BASE MODELS ====================

class UserLoginBase(BaseModel):
    """Base fields for users_login table."""
    email: EmailStr
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone_number: Optional[str] = None
    phone_verification: Optional[bool] = False
    is_active: Optional[bool] = True
    email_verified: Optional[bool] = False
    remember_me: Optional[bool] = False
    remember_token: Optional[str] = None
    remember_token_expires_at: Optional[datetime] = None


class UserProfileBase(BaseModel):
    """Base fields for users_profile_login table."""
    location: Optional[str] = None
    profile_image_url: Optional[str] = None
    oauth_provider: Optional[str] = None
    oauth_id: Optional[str] = None
    is_anonym: Optional[bool] = False


# ==================== AUTH REQUEST MODELS ====================

class UserRegister(UserLoginBase):
    """Request model for user registration."""
    password: str = Field(..., min_length=8)
    location: Optional[str] = None
    
    def get_login_data(self, hashed_password: str) -> dict:
        """Get data for users_login table insert."""
        return {
            "email": self.email,
            "password": hashed_password,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "phone_number": self.phone_number,
            "phone_verification": self.phone_verification,
            "is_active": self.is_active,
            "email_verified": self.email_verified,
            "remember_me": self.remember_me,
            "remember_token": None,
            "remember_token_expires_at": None,
            "acc_created_at": datetime.utcnow().isoformat(),
            "acc_updated_at": datetime.utcnow().isoformat()
        }


class UserLogin(BaseModel):
    """Request model for email/password login."""
    email: EmailStr
    password: str
    remember_me: Optional[bool] = False
    location: Optional[str] = None


class GoogleTokenRequest(BaseModel):
    """Request model for Google token verification."""
    token: str


class TokenLoginRequest(BaseModel):
    """Request model for remember token login."""
    remember_token: str


class UserUpdate(BaseModel):
    """Request model for updating user profile."""
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone_number: Optional[str] = None
    location: Optional[str] = None
    profile_image_url: Optional[str] = None


# ==================== OTP REQUEST MODELS ====================

class SendOTPRequest(BaseModel):
    """Request model for sending SMS OTP."""
    phone_number: str = Field(..., pattern=r'^\+\d{10,15}$')


class VerifyOTPRequest(BaseModel):
    """Request model for verifying SMS OTP."""
    phone_number: str = Field(..., pattern=r'^\+\d{10,15}$')
    otp_code: str = Field(..., min_length=6, max_length=6, pattern=r'^\d{6}$')


# ==================== PASSWORD RESET REQUEST MODELS ====================

class ForgotPasswordRequest(BaseModel):
    """Request model for requesting password reset OTP."""
    email: EmailStr


class VerifyResetOTPRequest(BaseModel):
    """Request model for verifying password reset OTP."""
    email: EmailStr
    otp: str


class ResetPasswordRequest(BaseModel):
    """Request model for resetting password with OTP."""
    email: EmailStr
    otp: str
    new_password: str = Field(..., min_length=8)


class ChangePasswordRequest(BaseModel):
    """Request model for changing password (authenticated users)."""
    current_password: str
    new_password: str = Field(..., min_length=8)
    confirm_new_password: str


# ==================== EMAIL VERIFICATION REQUEST MODELS ====================

class VerifyEmailRequest(BaseModel):
    """Request model for email verification."""
    email: EmailStr
    token: str


# ==================== RESPONSE MODELS ====================

class UserResponse(UserLoginBase, UserProfileBase):
    """Combined response model merging users_login and users_profile_login."""
    id: UUID
    user_id: Optional[UUID] = None
    acc_created_at: Optional[datetime] = None
    acc_updated_at: Optional[datetime] = None
    last_login: Optional[datetime] = None
    remember_token: Optional[str] = None
    remember_token_expires_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    """JWT token response."""
    access_token: str
    token_type: str


class AuthResponse(BaseModel):
    """Authentication response with token and user data."""
    access_token: str
    token_type: str
    user: UserResponse


class OTPResponse(BaseModel):
    """Response model for OTP operations."""
    success: bool
    message: str
    expires_at: Optional[str] = None


class PasswordResetResponse(BaseModel):
    """Response model for password reset operations."""
    success: bool
    message: str
