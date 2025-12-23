"""
Password Reset Router
Handles OTP-based password reset flow.
"""
from fastapi import APIRouter, HTTPException, Depends, Request
from supabase import Client

from app.models.otp_model import (
    ForgotPasswordRequest,
    VerifyResetOTPRequest,
    ResetPasswordRequest,
    PasswordResetResponse
)
from app.models.user_model import AuthResponse
from app.services.password_reset_service import PasswordResetService
from app.db.supabase_client import get_supabase, get_supabase_admin
from app.core.security import create_access_token
from datetime import datetime


router = APIRouter(prefix="/auth", tags=["Password Reset"])


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
    try:
        print(f"DEBUG: Forgot password request for: {request.email}")
        result = PasswordResetService.request_password_reset(request.email)
        print(f"DEBUG: Result: {result}")
        
        if not result["success"]:
            raise HTTPException(
                status_code=404 if "not found" in result.get("error", "").lower() else 500,
                detail=result.get("error", "Failed to process request")
            )
        
        return PasswordResetResponse(
            success=True,
            message=result["message"]
        )
    except HTTPException:
        raise
    except Exception as e:
        print(f"ERROR in forgot_password: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")


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


@router.post("/request-password-reset-link", response_model=PasswordResetResponse)
async def request_password_reset_link(request: ForgotPasswordRequest):
    """
    Step 1 (Magic Link): Request password reset via Email Link.
    
    - Validates user exists
    - Triggers Supabase Auth to send reset password email
    - Link redirects to frontend with access token
    
    Request Body:
        email: User's email address
        
    Returns:
        success: bool
        message: Status message
    """
    try:
        # Default redirect to frontend reset password page
        # You might want to make this configurable or take it from request if needed
        redirect_url = "http://localhost:5173/reset-password"
        
        result = PasswordResetService.request_password_reset_link(request.email, redirect_url)
        
        if not result["success"]:
            raise HTTPException(
                status_code=404 if "not found" in result.get("error", "").lower() else 400,
                detail=result.get("error", "Failed to send reset link")
            )
            
        return PasswordResetResponse(
            success=True,
            message=result["message"]
        )
    except HTTPException:
        raise
    except Exception as e:
        print(f"ERROR in request_password_reset_link: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")


@router.post("/reset-password", response_model=AuthResponse)
async def reset_password(
    request: ResetPasswordRequest,
    http_request: Request,
    supabase: Client = Depends(get_supabase),
    supabase_admin: Client = Depends(get_supabase_admin)
):
    """
    Step 3: Reset password with OTP.
    
    - Verifies OTP one last time
    - Hashes and updates user password
    - Invalidates OTP (single-use)
    - Returns access token and user data for immediate login
    
    Request Body:
        email: User's email
        otp: 6-digit OTP
        new_password: New password
    """
    try:
        print(f"DEBUG: Reset password request for: {request.email}")
        result = PasswordResetService.reset_password(
            request.email, 
            request.otp, 
            request.new_password
        )
        
        if not result["success"]:
            raise HTTPException(
                status_code=400,
                detail=result.get("error", "Failed to reset password")
            )
            
        # 4. Successful reset -> Auto-login
        # Get user from users_login
        user_res = supabase.table("users_login").select("*").eq("email", request.email).execute()
        if not user_res.data:
            raise HTTPException(status_code=404, detail="User not found after reset")
        
        user = user_res.data[0]
        
        # Update stats in users_profile_login (similar to login endpoint)
        try:
            profile_check = supabase.table("users_profile_login").select("*").eq("user_id", user["id"]).execute()
            current_time = datetime.utcnow().isoformat()
            
            if profile_check.data:
                current_count = profile_check.data[0].get("no_of_logins", 0) or 0
                supabase.table("users_profile_login").update({
                    "last_login": current_time,
                    "activity_time": current_time,
                    "ip_address": http_request.client.host,
                    "no_of_logins": current_count + 1
                }).eq("user_id", user["id"]).execute()
            else:
                supabase.table("users_profile_login").insert({
                    "user_id": user["id"],
                    "last_login": current_time,
                    "activity_time": current_time,
                    "ip_address": http_request.client.host,
                    "no_of_logins": 1
                }).execute()
        except Exception as e:
            print(f"Warning: Failed to update stats during reset login: {e}")
            
        # Generate token
        access_token = create_access_token(data={"sub": user["email"]})
        
        # Fetch shared profile
        profile_res = supabase.table("users_profile_login").select("*").eq("user_id", user["id"]).execute()
        user_profile = profile_res.data[0] if profile_res.data else {}
        
        combined_user = {**user, **user_profile}
        
        return {
            "access_token": access_token, 
            "token_type": "bearer",
            "user": combined_user
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"ERROR in reset_password: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")
