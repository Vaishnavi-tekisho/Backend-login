"""
User Router
Handles user profile operations.
"""
from fastapi import APIRouter, Depends, HTTPException

from app.db.supabase_client import get_supabase, get_supabase_admin, Client
from app.middleware.auth_middleware import get_current_user
from app.models.user_model import UserResponse, UserUpdate, ChangePasswordRequest
from app.core.security import verify_password, get_password_hash
from datetime import datetime, timedelta


router = APIRouter(prefix="/users", tags=["Users"])


@router.post("/change-password")
async def change_password(
    request: ChangePasswordRequest,
    current_user: dict = Depends(get_current_user),
    supabase_admin: Client = Depends(get_supabase_admin)
):
    """
    Change user password while authenticated.
    Requires current_password for verification.
    """
    try:
        user_id = current_user["id"]
        email = current_user["email"]
        
        # 1. Fetch user profile for OAuth check and Rate Limiting
        profile_res = supabase_admin.table("users_profile_login").select(
            "oauth_provider, password_change_attempts, last_password_change_attempt"
        ).eq("user_id", user_id).execute()
        
        profile = profile_res.data[0] if profile_res.data else {}
        oauth_provider = profile.get("oauth_provider")
        attempts = profile.get("password_change_attempts") or 0
        last_attempt_str = profile.get("last_password_change_attempt")
        
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
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/me", response_model=UserResponse)
async def get_my_profile(current_user: dict = Depends(get_current_user)):
    """Get current user's profile."""
    return current_user


@router.put("/me", response_model=UserResponse)
async def update_my_profile(
    user_update: UserUpdate,
    current_user: dict = Depends(get_current_user),
    supabase: Client = Depends(get_supabase)
):
    """Update current user's profile."""
    try:
        update_data = user_update.model_dump(exclude_unset=True)
        
        if not update_data:
            raise HTTPException(status_code=400, detail="No data to update")
        
        result = supabase.table("users_login").update(update_data).eq("id", current_user["id"]).execute()
        
        if not result.data:
            raise HTTPException(status_code=500, detail="Failed to update profile")
        
        return result.data[0]
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{user_id}", response_model=UserResponse)
async def get_user_by_id(
    user_id: str,
    current_user: dict = Depends(get_current_user),
    supabase: Client = Depends(get_supabase)
):
    """Get user by ID (admin only or self)."""
    try:
        result = supabase.table("users_login").select("*").eq("id", user_id).execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="User not found")
        
        return result.data[0]
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
