"""
Auth Router
API endpoints for authentication, user management, password reset, and OTP operations.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Request, BackgroundTasks
from fastapi.responses import RedirectResponse
import httpx
import secrets

from src.core.database import get_supabase, get_supabase_admin, Client
from src.core.middleware import get_current_user, get_current_active_user
from src.core.exceptions import (
    DuplicateEmailError,
    InvalidCredentialsError,
    InvalidTokenError,
    InactiveUserError,
    UserNotFoundError,
    InvalidOTPError,
    PasswordResetError
)
from src.modules.auth.schemas import (
    UserRegister,
    UserLogin,
    GoogleTokenRequest,
    TokenLoginRequest,
    UserUpdate,
    UserResponse,
    AuthResponse,
    SendOTPRequest,
    VerifyOTPRequest,
    ForgotPasswordRequest,
    VerifyResetOTPRequest,
    ResetPasswordRequest,
    ChangePasswordRequest,
    VerifyEmailRequest,
    OTPResponse,
    PasswordResetResponse
)
from src.modules.auth.service import (
    AuthService,
    PasswordResetService,
    VerificationService,
    OTPService,
    EmailService
)
from src.modules.auth.repository import UserRepository, UserProfileRepository
from src.core.config import settings


router = APIRouter(tags=["Auth"])


# ==================== DEBUG ENDPOINT ====================

@router.get("/auth/debug-google")
async def debug_google_config():
    """Debug endpoint to check Google OAuth configuration."""
    return {
        "client_id": settings.GOOGLE_CLIENT_ID[:20] + "..." if settings.GOOGLE_CLIENT_ID else None,
        "redirect_uri": settings.GOOGLE_REDIRECT_URI,
        "has_secret": bool(settings.GOOGLE_CLIENT_SECRET)
    }


# ==================== SIGNUP & EMAIL VERIFICATION ====================

@router.post("/auth/signup", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
async def register(user_in: UserRegister, request: Request, background_tasks: BackgroundTasks):
    """
    Register a new user.
    Creates entries in both users_login and users_profile_login tables.
    """
    success, user, message = AuthService.register_user(
        email=user_in.email,
        password=user_in.password,
        first_name=user_in.first_name,
        last_name=user_in.last_name,
        phone_number=user_in.phone_number,
        location=user_in.location,
        client_host=request.client.host
    )
    
    if not success:
        if "already registered" in message:
            raise DuplicateEmailError(detail=message)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=message)
    
    # Trigger Email Verification
    background_tasks.add_task(VerificationService.request_verification_email, user_in.email)
    
    return {
        "access_token": None,
        "token_type": None,
        "user": user
    }


@router.post("/auth/request-verification")
async def request_verification(email: str):
    """Request email verification link."""
    redirect_url = "http://localhost:5173/login/verification-success"
    result = VerificationService.request_verification_email(email, redirect_url)
    
    if not result["success"]:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=result.get("error"))
    
    return result


@router.post("/auth/verify-email")
async def verify_email_endpoint(request: VerifyEmailRequest):
    """Verify email with token."""
    result = VerificationService.verify_email(request.email, request.token)
    
    if not result["success"]:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=result.get("error"))
    
    return result


# ==================== LOGIN ====================

@router.post("/auth/login", response_model=AuthResponse)
async def login(user_in: UserLogin, request: Request, background_tasks: BackgroundTasks):
    """
    Login with email and password.
    """
    success, user, access_token, message = AuthService.login_user(
        email=user_in.email,
        password=user_in.password,
        remember_me=user_in.remember_me,
        location=user_in.location,
        client_host=request.client.host
    )
    
    if not success:
        raise InvalidCredentialsError(detail=message)
    
    # Send login success email
    background_tasks.add_task(EmailService.send_login_success_email, user_in.email, {"first_name": user.get("first_name", "")})
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": user
    }


@router.post("/auth/login/token", response_model=AuthResponse)
async def login_with_token(request: TokenLoginRequest, request_obj: Request, background_tasks: BackgroundTasks):
    """
    Login using remember token.
    """
    user = UserRepository.get_by_id(request.remember_token)
    # This is simplified - actual implementation should validate token expiry
    
    if not user:
        raise InvalidTokenError(detail="Invalid remember token")
    
    profile = UserProfileRepository.get_by_user_id(user["id"])
    combined_user = {**user, **(profile or {})}
    
    from src.core.security import create_access_token
    access_token = create_access_token(data={"sub": user["email"]})
    
    # Send login success email
    background_tasks.add_task(EmailService.send_login_success_email, user["email"], {"first_name": user.get("first_name", "")})
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": combined_user
    }


# ==================== GOOGLE OAUTH ====================

@router.get("/auth/google")
async def google_login(request: Request):
    """Redirect to Google OAuth consent screen."""
    from urllib.parse import urlencode
    
    params = {
        "client_id": settings.GOOGLE_CLIENT_ID,
        "redirect_uri": settings.GOOGLE_REDIRECT_URI,
        "response_type": "code",
        "scope": "openid email profile"
    }
    
    google_auth_url = f"https://accounts.google.com/o/oauth2/v2/auth?{urlencode(params)}"
    return RedirectResponse(url=google_auth_url)


@router.get("/auth/google/callback")
async def google_callback(code: str, request: Request, background_tasks: BackgroundTasks):
    """
    Handle Google OAuth callback.
    Exchanges code for token and creates/logs in user.
    """
    try:
        # Exchange code for token
        async with httpx.AsyncClient() as client:
            token_response = await client.post(
                "https://oauth2.googleapis.com/token",
                data={
                    "client_id": settings.GOOGLE_CLIENT_ID,
                    "client_secret": settings.GOOGLE_CLIENT_SECRET,
                    "code": code,
                    "grant_type": "authorization_code",
                    "redirect_uri": settings.GOOGLE_REDIRECT_URI
                }
            )
            token_data = token_response.json()
            access_token = token_data.get("access_token")
        
        if not access_token:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Failed to get access token")
        
        # Get user info from Google
        async with httpx.AsyncClient() as client:
            user_info_response = await client.get(
                "https://www.googleapis.com/oauth2/v2/userinfo",
                headers={"Authorization": f"Bearer {access_token}"}
            )
            user_info = user_info_response.json()
        
        email = user_info.get("email")
        name = user_info.get("name", "").split(" ")
        first_name = name[0] if name else ""
        last_name = name[1] if len(name) > 1 else ""
        
        # Check if user exists, if not create
        existing_user = UserRepository.get_by_email(email)
        if existing_user:
            user = existing_user
        else:
            success, user, _ = AuthService.register_user(
                email=email,
                password=secrets.token_urlsafe(32),  # Random password for OAuth users
                first_name=first_name,
                last_name=last_name,
                client_host=request.client.host
            )
            if not success:
                raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to create user")
        
        # Get user profile
        profile = UserProfileRepository.get_by_user_id(user["id"])
        if profile:
            UserProfileRepository.update(user["id"], {"oauth_provider": "google", "oauth_id": user_info.get("id")})
        else:
            UserProfileRepository.create({
                "user_id": user["id"],
                "oauth_provider": "google",
                "oauth_id": user_info.get("id")
            })
        
        # Create JWT token
        from src.core.security import create_access_token
        jwt_token = create_access_token(data={"sub": email})
        
        # Send login success email
        background_tasks.add_task(EmailService.send_login_success_email, email, {"first_name": user.get("first_name", "")})
        
        # Redirect to frontend with token
        redirect_url = f"http://localhost:5173?access_token={jwt_token}&token_type=bearer"
        return RedirectResponse(url=redirect_url)
    
    except Exception as e:
        print(f"Error in Google callback: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/auth/google", response_model=AuthResponse)
async def verify_google_token(request: GoogleTokenRequest, request_obj: Request, background_tasks: BackgroundTasks):
    """
    Verify Google ID token and login/create user.
    """
    try:
        from google.auth.transport import requests
        from google.oauth2 import id_token
        
        idinfo = id_token.verify_oauth2_token(request.token, requests.Request(), settings.GOOGLE_CLIENT_ID)
        
        email = idinfo.get("email")
        name = idinfo.get("name", "").split(" ")
        first_name = name[0] if name else ""
        last_name = name[1] if len(name) > 1 else ""
        
        # Check if user exists
        existing_user = UserRepository.get_by_email(email)
        if existing_user:
            user = existing_user
        else:
            import secrets
            success, user, _ = AuthService.register_user(
                email=email,
                password=secrets.token_urlsafe(32),
                first_name=first_name,
                last_name=last_name,
                client_host=request_obj.client.host
            )
            if not success:
                raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to create user")
        
        # Update profile with OAuth info
        profile = UserProfileRepository.get_by_user_id(user["id"])
        if profile:
            UserProfileRepository.update(user["id"], {"oauth_provider": "google", "oauth_id": idinfo.get("sub")})
        else:
            UserProfileRepository.create({
                "user_id": user["id"],
                "oauth_provider": "google",
                "oauth_id": idinfo.get("sub")
            })
        
        # Get updated profile
        profile = UserProfileRepository.get_by_user_id(user["id"])
        combined_user = {**user, **(profile or {})}
        
        from src.core.security import create_access_token
        access_token = create_access_token(data={"sub": email})
        
        # Send login success email
        background_tasks.add_task(EmailService.send_login_success_email, email, {"first_name": user.get("first_name", "")})
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": combined_user
        }
    except Exception as e:
        print(f"Error verifying Google token: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid Google token")


# ==================== USER PROFILE ====================

@router.get("/auth/me", response_model=UserResponse)
async def get_current_user_info(current_user: dict = Depends(get_current_active_user)):
    """Get current authenticated user's profile."""
    return current_user


@router.get("/users/me", response_model=UserResponse)
async def get_my_profile(current_user: dict = Depends(get_current_active_user)):
    """Get current user's profile."""
    return current_user


@router.put("/users/me", response_model=UserResponse)
async def update_my_profile(
    user_update: UserUpdate,
    current_user: dict = Depends(get_current_active_user),
    supabase: Client = Depends(get_supabase)
):
    """Update current user's profile."""
    try:
        update_data = user_update.model_dump(exclude_unset=True)
        
        if not update_data:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No data to update")
        
        result = supabase.table("users_login").update(update_data).eq("id", current_user["id"]).execute()
        
        if not result.data:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to update profile")
        
        return result.data[0]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/users/{user_id}", response_model=UserResponse)
async def get_user_by_id(
    user_id: str,
    current_user: dict = Depends(get_current_active_user),
    supabase: Client = Depends(get_supabase)
):
    """Get user by ID (requires authentication)."""
    try:
        result = supabase.table("users_login").select("*").eq("id", user_id).execute()
        
        if not result.data:
            raise UserNotFoundError()
        
        return result.data[0]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


# ==================== PASSWORD RESET ====================

@router.post("/auth/forgot-password", response_model=PasswordResetResponse)
async def forgot_password(request: ForgotPasswordRequest):
    """
    Request password reset via OTP.
    
    Step 1: Validate user exists, generate OTP, send via email.
    """
    result = PasswordResetService.request_password_reset(request.email)
    
    if not result["success"]:
        # Return 404 if user not found, 500 for other errors
        status_code = status.HTTP_404_NOT_FOUND if "not found" in result.get("error", "").lower() else status.HTTP_500_INTERNAL_SERVER_ERROR
        raise HTTPException(status_code=status_code, detail=result.get("error"))
    
    return PasswordResetResponse(success=True, message=result["message"])


@router.post("/auth/verify-reset-otp", response_model=PasswordResetResponse)
async def verify_reset_otp(request: VerifyResetOTPRequest):
    """
    Verify password reset OTP.
    
    Step 2: Check OTP validity and expiry (doesn't invalidate OTP yet).
    """
    result = PasswordResetService.verify_reset_otp(request.email, request.otp)
    
    if not result["success"]:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=result.get("error"))
    
    return PasswordResetResponse(success=True, message=result["message"])


@router.post("/auth/reset-password", response_model=PasswordResetResponse)
async def reset_password(request: ResetPasswordRequest):
    """
    Reset password with OTP.
    
    Step 3: Re-verify OTP, update password, invalidate OTP.
    """
    result = PasswordResetService.reset_password(
        request.email,
        request.otp,
        request.new_password
    )
    
    if not result["success"]:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=result.get("error"))
    
    return PasswordResetResponse(success=True, message=result["message"])


@router.post("/auth/request-password-reset-link", response_model=PasswordResetResponse)
async def request_password_reset_link(request: ForgotPasswordRequest):
    """
    Request password reset via magic link.
    
    Alternative to OTP: sends secure link via email.
    """
    redirect_url = "http://localhost:5173/reset-password"
    result = PasswordResetService.request_password_reset_link(request.email, redirect_url)
    
    if not result["success"]:
        status_code = status.HTTP_404_NOT_FOUND if "not found" in result.get("error", "").lower() else status.HTTP_500_INTERNAL_SERVER_ERROR
        raise HTTPException(status_code=status_code, detail=result.get("error"))
    
    return PasswordResetResponse(success=True, message=result["message"])


# ==================== OTP (SMS) ====================

@router.post("/auth/send-otp", response_model=OTPResponse)
async def send_otp(request: SendOTPRequest):
    """
    Send OTP to phone number via SMS (Twilio).
    """
    result = OTPService.send_otp(request.phone_number)
    
    if not result["success"]:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=result["message"])
    
    return OTPResponse(
        success=result["success"],
        message=result["message"]
    )


@router.post("/auth/verify-otp", response_model=OTPResponse)
async def verify_otp(request: VerifyOTPRequest):
    """
    Verify OTP code sent to phone number (Twilio).
    """
    result = OTPService.verify_otp(request.phone_number, request.otp_code)
    
    if not result["success"]:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=result["message"])
    
    return OTPResponse(
        success=result["success"],
        message=result["message"]
    )


# ==================== CHANGE PASSWORD (AUTHENTICATED) ====================

@router.post("/users/change-password")
async def change_password(
    request: ChangePasswordRequest,
    current_user: dict = Depends(get_current_user),
    supabase_admin: Client = Depends(get_supabase_admin)
):
    """
    Change password for authenticated user.
    
    - Requires current password verification
    - Only for email-based accounts (not OAuth)
    - Rate limited: 5 attempts per hour
    - Invalidates existing sessions on success
    """
    try:
        from src.core.security import verify_password, get_password_hash
        from datetime import datetime, timedelta
        
        user_id = current_user["id"]
        email = current_user["email"]
        
        # Validate passwords match
        if request.new_password != request.confirm_new_password:
            raise HTTPException(status_code=400, detail="New passwords do not match")
        
        # Validate new password is different
        # 1. Fetch user profile for OAuth check and Rate Limiting
        profile_res = supabase_admin.table("users_profile_login").select(
            "oauth_provider, password_change_attempts, last_password_change_attempt"
        ).eq("user_id", user_id).execute()
        
        profile = profile_res.data[0] if profile_res.data else {}
        oauth_provider = profile.get("oauth_provider")
        attempts = profile.get("password_change_attempts") or 0
        last_attempt_str = profile.get("last_password_change_attempt")
        
        # Check OAuth
        if oauth_provider and oauth_provider != "email":
            raise HTTPException(
                status_code=400, 
                detail=f"Accounts using {oauth_provider} should use 'Set Password'. Password change is for email accounts only."
            )

        # Rate Limiting: Max 5 per hour
        now_dt = datetime.utcnow()
        if last_attempt_str:
            last_attempt = datetime.fromisoformat(last_attempt_str.replace('Z', '+00:00')).replace(tzinfo=None)
            if now_dt - last_attempt < timedelta(hours=1):
                if attempts >= 5:
                    raise HTTPException(
                        status_code=429, 
                        detail="Too many password change attempts. Please try again in an hour."
                    )
            else:
                # Reset attempts if more than an hour has passed
                attempts = 0

        # Increment attempts
        supabase_admin.table("users_profile_login").update({
            "password_change_attempts": attempts + 1,
            "last_password_change_attempt": now_dt.isoformat()
        }).eq("user_id", user_id).execute()

        # 2. Fetch current password hash
        response = supabase_admin.table("users_login").select("password").eq("id", user_id).execute()
        if not response.data:
            raise HTTPException(status_code=404, detail="User not found")
            
        hashed_password = response.data[0].get("password")
        
        # 3. Verify current password
        if not verify_password(request.current_password, hashed_password):
            raise HTTPException(status_code=400, detail="Incorrect current password")
        
        # Check if new password is same as current
        if verify_password(request.new_password, hashed_password):
            raise HTTPException(status_code=400, detail="New password cannot be the same as current password")
            
        # 4. Hash new password
        new_hashed_password = get_password_hash(request.new_password)
        
        # 5. Update database and invalidate remember tokens
        now = datetime.utcnow().isoformat()
        update_result = supabase_admin.table("users_login").update({
            "password": new_hashed_password,
            "password_updated_at": now,
            "acc_updated_at": now,
            "remember_token": None,
            "remember_token_expires_at": None
        }).eq("id", user_id).execute()
        
        if not update_result.data:
            raise HTTPException(status_code=500, detail="Failed to update password")
            
        return {"success": True, "message": "Password changed successfully. Existing sessions have been invalidated."}
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"ERROR in change_password: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

