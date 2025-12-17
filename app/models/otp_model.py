"""
OTP Models
Pydantic models for OTP-related API requests and responses.
"""
from pydantic import BaseModel, EmailStr, Field


# ==================== REQUEST MODELS ====================

class SendOTPRequest(BaseModel):
    """Request model for sending OTP via SMS."""
    phone_number: str = Field(..., pattern=r'^\+\d{10,15}$')


class VerifyOTPRequest(BaseModel):
    """Request model for verifying SMS OTP."""
    phone_number: str = Field(..., pattern=r'^\+\d{10,15}$')
    otp_code: str = Field(..., min_length=6, max_length=6, pattern=r'^\d{6}$')


class ForgotPasswordRequest(BaseModel):
    """Request model for requesting password reset OTP."""
    email: EmailStr


class VerifyResetOTPRequest(BaseModel):
    """Request model for verifying password reset OTP."""
    email: EmailStr
    otp: str = Field(..., min_length=6, max_length=6, pattern=r'^\d{6}$')


class ResetPasswordRequest(BaseModel):
    """Request model for resetting password with OTP."""
    email: EmailStr
    otp: str = Field(..., min_length=6, max_length=6, pattern=r'^\d{6}$')
    new_password: str = Field(..., min_length=8)


class ResetPasswordConfirm(BaseModel):
    """Request model for Supabase token-based password reset."""
    new_password: str
    supabase_access_token: str


# ==================== RESPONSE MODELS ====================

class OTPResponse(BaseModel):
    """Response model for OTP operations."""
    success: bool
    message: str
    expires_at: str | None = None


class PasswordResetResponse(BaseModel):
    """Response model for password reset operations."""
    success: bool
    message: str
