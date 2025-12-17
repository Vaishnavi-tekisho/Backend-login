from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime, date
from uuid import UUID

# Shared properties
class UserBase(BaseModel):
    email: EmailStr
    user_name: Optional[str] = None
    phone_number: Optional[str] = None
    location: Optional[str] = None

# Properties to create a user via registration
class UserCreate(UserBase):
    password: str

# Properties to create a user via Google
class UserCreateGoogle(UserBase):
    password: Optional[str] = None
    oauth_provider: str = "google"
    profile_image_url: Optional[str] = None
    oauth_id: Optional[str] = None

# Properties used when logging in
class UserLogin(BaseModel):
    email: EmailStr
    password: str

# Properties returned to client
class UserResponse(UserBase):
    id: int
    profile_image_url: Optional[str]
    acc_created_at: Optional[datetime]
    is_active: bool
    email_verified: bool
    oauth_provider: Optional[str]
    
    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None
    user_id: Optional[UUID] = None

class AuthResponse(BaseModel):
    access_token: str
    token_type: str
    user: UserResponse

# OTP Schemas
from typing import Optional
from pydantic import BaseModel, Field

# OTP Schemas
class SendOTPRequest(BaseModel):
    phone_number: str = Field(..., pattern=r'^\+\d{10,15}$')

class ForgotPasswordRequest(BaseModel):
    email: EmailStr

class ResetPasswordConfirm(BaseModel):
    new_password: str
    supabase_access_token: str

class VerifyOTPRequest(BaseModel):
    phone_number: str = Field(..., pattern=r'^\+\d{10,15}$')
    otp_code: str = Field(..., min_length=6, max_length=6, pattern=r'^\d{6}$')

class VerifyResetOTPRequest(BaseModel):
    email: EmailStr
    otp: str = Field(..., min_length=6, max_length=6, pattern=r'^\d{6}$')

class ResetPasswordWithOTPRequest(BaseModel):
    email: EmailStr
    otp: str = Field(..., min_length=6, max_length=6, pattern=r'^\d{6}$')
    new_password: str = Field(..., min_length=8)

class OTPResponse(BaseModel):
    success: bool
    message: str
    expires_at: str | None = None

class ResetPasswordRequest(BaseModel):
    email: EmailStr
    otp: str
    new_password: str

