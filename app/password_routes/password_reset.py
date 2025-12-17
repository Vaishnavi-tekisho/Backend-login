"""
Password Reset Routes
Clean endpoints for OTP-based password reset flow.
Controllers only - business logic in services.
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr, Field

from app.services.password_reset_service import PasswordResetService


router = APIRouter(prefix="/auth", tags=["Password Reset"])


# ==================== REQUEST SCHEMAS ====================

class ForgotPasswordRequest(BaseModel):
    """Request schema for forgot password endpoint."""
    email: EmailStr


class VerifyResetOTPRequest(BaseModel):
    """Request schema for OTP verification endpoint."""
    email: EmailStr
    otp: str = Field(..., min_length=6, max_length=6, pattern=r'^\d{6}$')


class ResetPasswordRequest(BaseModel):
    """Request schema for password reset endpoint."""
    email: EmailStr
    otp: str = Field(..., min_length=6, max_length=6, pattern=r'^\d{6}$')
    new_password: str = Field(..., min_length=8)


# ==================== RESPONSE SCHEMAS ====================

class PasswordResetResponse(BaseModel):
    """Standard response schema for password reset endpoints."""
    success: bool
    message: str


# ==================== ROUTE HANDLERS ====================

@router.post("/forgot-password", response_model=PasswordResetResponse)
async def forgot_password(request: ForgotPasswordRequest):
    """
    Step 1: Request password reset OTP.
    
    - Validates user exists
    - Generates 6-digit OTP
    - Hashes and stores OTP with 5-minute expiry
    - Sends OTP via email
    
    Request Body:
        email: User's email address
        
    Returns:
        success: bool
        message: Status message
    """
    result = PasswordResetService.request_password_reset(request.email)
    
    if not result["success"]:
        raise HTTPException(
            status_code=404 if "not found" in result.get("error", "").lower() else 500,
            detail=result.get("error", "Failed to process request")
        )
    
    return PasswordResetResponse(
        success=True,
        message=result["message"]
    )


@router.post("/verify-reset-otp", response_model=PasswordResetResponse)
async def verify_reset_otp(request: VerifyResetOTPRequest):
    """
    Step 2: Verify password reset OTP.
    
    - Checks OTP validity
    - Checks OTP expiry (5 minutes)
    - Does NOT issue any token/session
    - OTP remains valid for password reset step
    
    Request Body:
        email: User's email address
        otp: 6-digit OTP from email
        
    Returns:
        success: bool
        message: Status message
    """
    result = PasswordResetService.verify_reset_otp(request.email, request.otp)
    
    if not result["success"]:
        raise HTTPException(
            status_code=400,
            detail=result.get("error", "OTP verification failed")
        )
    
    return PasswordResetResponse(
        success=True,
        message=result["message"]
    )


@router.post("/reset-password", response_model=PasswordResetResponse)
async def reset_password(request: ResetPasswordRequest):
    """
    Step 3: Reset password with OTP.
    
    - Re-verifies OTP (security)
    - Updates password in database
    - Invalidates OTP (single-use)
    
    Request Body:
        email: User's email address
        otp: 6-digit OTP from email
        new_password: New password (min 8 characters)
        
    Returns:
        success: bool
        message: Status message
    """
    result = PasswordResetService.reset_password(
        request.email, 
        request.otp, 
        request.new_password
    )
    
    if not result["success"]:
        raise HTTPException(
            status_code=400,
            detail=result.get("error", "Password reset failed")
        )
    
    return PasswordResetResponse(
        success=True,
        message=result["message"]
    )
