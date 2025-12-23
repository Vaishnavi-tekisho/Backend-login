"""
Authentication Router
Handles signup, login, and OAuth authentication endpoints.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Request, BackgroundTasks
from fastapi.responses import RedirectResponse
import httpx
from datetime import datetime
import json
import urllib.parse

from app.core.config import settings
from app.core.security import create_access_token, verify_password, get_password_hash
from app.db.supabase_client import get_supabase, get_supabase_admin, Client
from app.models.user_model import (
    UserCreate, 
    UserLogin, 
    GoogleTokenRequest, 
    AuthResponse, 
    UserResponse,
    TokenLoginRequest
)
from app.middleware.auth_middleware import get_current_user


router = APIRouter(prefix="/auth", tags=["Authentication"])


# ==================== SIGNUP ====================

@router.post("/signup", response_model=AuthResponse)
async def register(user_in: UserCreate, request: Request, supabase: Client = Depends(get_supabase)):
    """
    Register a new user.
    Creates entries in both users_login and users_profile_login.
    """
    try:
        # 1. Check if user already exists
        existing = supabase.table("users_login").select("id").eq("email", user_in.email).execute()
        if existing.data:
            raise HTTPException(status_code=400, detail="Email already registered")

        # 2. Hash password
        hashed_pw = get_password_hash(user_in.password)
        
        # 3. Create Login Data (users_login)
        login_data = user_in.get_login_data(hashed_pw)
        
        print(f"DEBUG: Inserting into users_login: {login_data['email']}")
        login_response = supabase.table("users_login").insert(login_data).execute()
        
        if not login_response.data:
             raise HTTPException(status_code=500, detail="Failed to create user login record")
             
        user_login = login_response.data[0]
        user_id = user_login["id"]

        # 4. Create Profile Data (users_profile_login)
        profile_data = {
            "user_id": user_id,
            "location": user_in.location,
            "ip_address": request.client.host,
            "oauth_provider": "email",
            "last_login": datetime.utcnow().isoformat(),
            "activity_time": datetime.utcnow().isoformat(),
            "no_of_logins": 1
        }
        
        print(f"DEBUG: Inserting into users_profile_login for user_id: {user_id}")
        profile_response = supabase.table("users_profile_login").insert(profile_data).execute()
        
        # 5. Combine for response
        user_profile = profile_response.data[0] if profile_response.data else {}
        user_response = {**user_login, **user_profile}
        
        # 6. Trigger Email Verification
        from app.services.verification_service import VerificationService
        VerificationService.request_verification_email(user_login["email"])
        
        access_token = create_access_token(data={"sub": user_login["email"]})
        
        return {
            "access_token": access_token, 
            "token_type": "bearer",
            "user": user_response
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"Exception during registration: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal Error: {str(e)}")
@router.post("/request-verification")
async def request_verification(email: str):
    """Request email verification link (Resend)."""
    from app.services.verification_service import VerificationService
    result = VerificationService.request_verification_email(email)
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@router.get("/verify-email")
async def verify_email(token: str, email: str):
    """Verify email using token."""
    from app.services.verification_service import VerificationService
    result = VerificationService.verify_email(email, token)
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])
    return result

@router.post("/verify-email")
async def verify_email_endpoint(email: str, token: str):
    """Verify email with token."""
    from app.services.verification_service import VerificationService
    result = VerificationService.verify_email(email, token)
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


from app.services.email_service import EmailService


# ==================== LOGIN ====================

@router.post("/login", response_model=AuthResponse)
async def login(
    user_in: UserLogin, 
    request: Request, 
    background_tasks: BackgroundTasks,
    supabase: Client = Depends(get_supabase), 
    supabase_admin: Client = Depends(get_supabase_admin)
):
    """
    Login with email and password.
    """
    # 1. Get user from users_login
    # Use admin client to bypass RLS for user lookup
    response = supabase_admin.table("users_login").select("*").eq("email", user_in.email).execute()
    print(f"DEBUG LOGIN: User lookup result count: {len(response.data) if response.data else 0}")
    user = response.data[0] if response.data else None
    
    # 2. Verify
    if not user or not user.get("password") or not verify_password(user_in.password, user["password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 3. Update stats in users_profile_login
    try:
        # Check if profile exists
        profile_check = supabase.table("users_profile_login").select("*").eq("user_id", user["id"]).execute()
        
        current_time = datetime.utcnow().isoformat()
        
        if profile_check.data:
            current_count = profile_check.data[0].get("no_of_logins", 0) or 0
            
            update_data = {
                "last_login": current_time,
                "activity_time": current_time,
                "ip_address": request.client.host,
                "no_of_logins": current_count + 1
            }
            if user_in.location:
                update_data["location"] = user_in.location
                
            supabase.table("users_profile_login").update(update_data).eq("user_id", user["id"]).execute()
        else:
            # Create profile if missing (resilience)
            insert_data = {
                "user_id": user["id"],
                "last_login": current_time,
                "activity_time": current_time,
                "ip_address": request.client.host,
                "no_of_logins": 1
            }
            if user_in.location:
                insert_data["location"] = user_in.location
                
            supabase.table("users_profile_login").insert(insert_data).execute()
            
    except Exception as e:
        print(f"Warning: Failed to update stats: {e}")

    # 4. Token
    access_token = create_access_token(data={"sub": user["email"]})
    
    # Handle Remember Me
    if user_in.remember_me:
        import secrets
        from datetime import timedelta
        
        remember_token = secrets.token_urlsafe(32)
        expires_at = datetime.utcnow() + timedelta(days=30)
        
        try:
            supabase_admin.table("users_login").update({
                "remember_me": True,
                "remember_token": remember_token,
                "remember_token_expires_at": expires_at.isoformat()
            }).eq("id", user["id"]).execute()
            
            # Update user dict for response
            user["remember_me"] = True
            user["remember_token"] = remember_token
            user["remember_token_expires_at"] = expires_at.isoformat()
            
        except Exception as e:
            print(f"Warning: Failed to set remember_token: {e}")

    # 5. Fetch Profile for Response
    profile_res = supabase.table("users_profile_login").select("*").eq("user_id", user["id"]).execute()
    user_profile = profile_res.data[0] if profile_res.data else {}
    
    combined_user = {**user, **user_profile}
    
    # Trigger login success email
    user_context = {
        "name": f"{user.get('first_name', '')} {user.get('last_name', '')}".strip() or "User",
        "ip_address": request.client.host
    }
    background_tasks.add_task(EmailService.send_login_success_email, user["email"], user_context)
    
    return {
        "access_token": access_token, 
        "token_type": "bearer",
        "user": combined_user
    }





@router.post("/login/token", response_model=AuthResponse)
async def login_via_token(
    token_req: TokenLoginRequest, 
    request: Request, 
    background_tasks: BackgroundTasks,
    supabase: Client = Depends(get_supabase), 
    supabase_admin: Client = Depends(get_supabase_admin)
):
    """
    Login using a remember_token.
    """
    token = token_req.remember_token
    current_time = datetime.utcnow()
    
    # 1. Find user by token
    # Reading is usually fine with regular client if RLS allows reading own data, 
    # but initially we might not have user context. 
    # Safest to use admin for lookup too if finding by token is restricted.
    response = supabase_admin.table("users_login").select("*").eq("remember_token", token).execute()
    user = response.data[0] if response.data else None
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid remember token",
        )
        
    # 2. Check Expiration
    expires_at_str = user.get("remember_token_expires_at")
    if not expires_at_str:
        raise HTTPException(status_code=401, detail="Token invalid")
        
    # Handle both string and datetime object if the driver returns it parsed
    if isinstance(expires_at_str, str):
        expires_at = datetime.fromisoformat(expires_at_str.replace('Z', '+00:00'))
    else:
        expires_at = expires_at_str

    if expires_at.tzinfo is None:
        # If naive, assume UTC
        pass 
    
    # Compare with current time (naive or aware)
    if expires_at.tzinfo and current_time.tzinfo is None:
        current_time = current_time.replace(tzinfo=expires_at.tzinfo)

    if expires_at < current_time:
         raise HTTPException(status_code=401, detail="Token expired")

    # 3. Rotate Token (Security Best Practice)
    import secrets
    from datetime import timedelta
    new_token = secrets.token_urlsafe(32)
    new_expires = datetime.utcnow() + timedelta(days=30)
    
    try:
        supabase_admin.table("users_login").update({
            "remember_token": new_token,
            "remember_token_expires_at": new_expires.isoformat()
        }).eq("id", user["id"]).execute()
        
        # Update user object
        user["remember_token"] = new_token
        user["remember_token_expires_at"] = new_expires.isoformat()
        
    except Exception as e:
        print(f"Warning: Failed to rotate token: {e}")

    # 4. Generate Access Token
    access_token = create_access_token(data={"sub": user["email"]})
    
    # 5. Fetch Profile
    profile_res = supabase.table("users_profile_login").select("*").eq("user_id", user["id"]).execute()
    user_profile = profile_res.data[0] if profile_res.data else {}
    
    combined_user = {**user, **user_profile}
    
    # Trigger login success email
    user_context = {
        "name": f"{user.get('first_name', '')} {user.get('last_name', '')}".strip() or "User",
        "ip_address": request.client.host
    }
    background_tasks.add_task(EmailService.send_login_success_email, user["email"], user_context)
    
    return {
        "access_token": access_token, 
        "token_type": "bearer",
        "user": combined_user
    }


# ==================== GOOGLE OAUTH ====================

@router.get("/google")
async def login_google():
    """Redirect to Google OAuth consent screen."""
    return RedirectResponse(
        url=f"https://accounts.google.com/o/oauth2/auth?response_type=code&client_id={settings.GOOGLE_CLIENT_ID}&redirect_uri={settings.GOOGLE_REDIRECT_URI}&scope=openid%20profile%20email&access_type=offline"
    )


@router.get("/callback")
async def auth_google_callback(code: str, request: Request, background_tasks: BackgroundTasks, supabase: Client = Depends(get_supabase)):
    """Handle Google OAuth callback."""
    try:
        print(f"DEBUG: Received callback with code: {code[:20]}...")
        
        token_url = "https://accounts.google.com/o/oauth2/token"
        data = {
            "code": code,
            "client_id": settings.GOOGLE_CLIENT_ID,
            "client_secret": settings.GOOGLE_CLIENT_SECRET,
            "redirect_uri": settings.GOOGLE_REDIRECT_URI,
            "grant_type": "authorization_code",
        }
        
        print(f"DEBUG: Exchanging code for token at {token_url}")
        async with httpx.AsyncClient() as client:
            response = await client.post(token_url, data=data)
            print(f"DEBUG: Token exchange response status: {response.status_code}")
            access_token_info = response.json()
            print(f"DEBUG: Token response keys: {access_token_info.keys()}")
            
        if "id_token" not in access_token_info:
            print(f"ERROR: No id_token in response. Full response: {access_token_info}")
            raise HTTPException(status_code=400, detail=f"Failed to retrieve token from Google: {access_token_info.get('error', 'Unknown error')}")
        
        print("DEBUG: Creating token request for verification")
        token_req = GoogleTokenRequest(token=access_token_info["id_token"])
        
        print("DEBUG: Calling google_verify")
        auth_result = await google_verify(token_req, request, background_tasks, supabase)
        
        print(f"DEBUG: Verification successful, user: {auth_result['user'].get('email')}")
        
        # Redirect to frontend with token and user data
        frontend_url = "http://localhost:5173/oauth-success"
        
        user_json = json.dumps(auth_result['user'], default=str)
        user_encoded = urllib.parse.quote(user_json)
        
        redirect_url = f"{frontend_url}?token={auth_result['access_token']}&user={user_encoded}"
        print(f"DEBUG: Redirecting to: {redirect_url[:100]}...")
        
        return RedirectResponse(url=redirect_url)
    
    except HTTPException:
        raise
    except Exception as e:
        print(f"ERROR in Google OAuth callback: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Internal error during OAuth: {str(e)}")


@router.post("/google", response_model=AuthResponse)
async def google_login(token_req: GoogleTokenRequest, request: Request, background_tasks: BackgroundTasks, supabase: Client = Depends(get_supabase)):
    """Verify Google Token and login/register user."""
    return await google_verify(token_req, request, background_tasks, supabase)


from app.db.supabase_client import get_supabase, get_supabase_admin

@router.post("/google-verify", response_model=AuthResponse)
async def google_verify(token_req: GoogleTokenRequest, request: Request, background_tasks: BackgroundTasks, supabase: Client = Depends(get_supabase)):
    """Verify Google ID token and creates/login user."""
    token = token_req.token
    
    async with httpx.AsyncClient() as client:
        resp = await client.get(f"https://oauth2.googleapis.com/tokeninfo?id_token={token}")
        
    if resp.status_code != 200:
        raise HTTPException(status_code=401, detail="Invalid Google Token")
        
    payload = resp.json()
    if settings.GOOGLE_CLIENT_ID and payload.get("aud") != settings.GOOGLE_CLIENT_ID:
        raise HTTPException(status_code=401, detail="Invalid Client ID in Token")

    email = payload.get("email")
    
    # Use Admin Client to bypass RLS for checking user existence
    supabase_admin = get_supabase_admin()
    
    # Check users_login
    response = supabase_admin.table("users_login").select("*").eq("email", email).execute()
    user = response.data[0] if response.data else None
    
    # Extract names from payload
    # prefer given_name/family_name, fallback to name split
    first_name = payload.get("given_name")
    last_name = payload.get("family_name")
    
    if not first_name:
        full_name = payload.get("name", "")
        name_parts = full_name.split(" ", 1) if full_name else ["", ""]
        first_name = name_parts[0] if name_parts else ""
        last_name = name_parts[1] if len(name_parts) > 1 else ""

    if not user:
        # REGISTER NEW USER
        
        # 1. Insert into users_login
        new_user_login = {
            "email": email,
            "password": "", # No password for OAuth
            "first_name": first_name,
            "last_name": last_name,
            "is_active": True,
            "email_verified": True,
            "acc_created_at": datetime.utcnow().isoformat(),
            "acc_updated_at": datetime.utcnow().isoformat()
        }
        data = supabase_admin.table("users_login").insert(new_user_login).execute()
        user = data.data[0]
        
        # 2. Insert into users_profile_login
        new_user_profile = {
            "user_id": user["id"],
            "profile_image_url": payload.get("picture"),
            "oauth_provider": "google",
            "oauth_id": payload.get("sub"),
            "ip_address": request.client.host,
            "last_login": datetime.utcnow().isoformat(),
            "activity_time": datetime.utcnow().isoformat(),
            "no_of_logins": 1
        }
        supabase_admin.table("users_profile_login").insert(new_user_profile).execute()
        
    else:
        # LOGIN EXISTING USER
        
        # Check if we should update names (if missing)
        updates = {}
        if not user.get("first_name") and first_name:
            updates["first_name"] = first_name
        if not user.get("last_name") and last_name:
            updates["last_name"] = last_name
            
        if updates:
             supabase_admin.table("users_login").update(updates).eq("id", user["id"]).execute()
             # Refresh user object
             user.update(updates)

        # Update users_profile_login
        profile_check = supabase_admin.table("users_profile_login").select("*").eq("user_id", user["id"]).execute()
        
        current_time = datetime.utcnow().isoformat()
        
        if profile_check.data:
            current_count = profile_check.data[0].get("no_of_logins", 0) or 0
            supabase_admin.table("users_profile_login").update({
                "last_login": current_time,
                "no_of_logins": current_count + 1
            }).eq("user_id", user["id"]).execute()
        else:
             supabase_admin.table("users_profile_login").insert({
                "user_id": user["id"],
                "last_login": current_time,
                "no_of_logins": 1,
                "oauth_provider": "google"
            }).execute()

    # Create Response
    access_token = create_access_token(data={"sub": user["email"]})
    
    profile_res = supabase_admin.table("users_profile_login").select("*").eq("user_id", user["id"]).execute()
    user_profile = profile_res.data[0] if profile_res.data else {}
    
    combined_user = {**user, **user_profile}

    # Trigger login success email (only if logging in, technically creation is also a login)
    user_context = {
        "name": f"{user.get('first_name', '')} {user.get('last_name', '')}".strip() or "User",
        "ip_address": request.client.host
    }
    background_tasks.add_task(EmailService.send_login_success_email, user["email"], user_context)

    return {
        "access_token": access_token, 
        "token_type": "bearer",
        "user": combined_user
    }


# ==================== CURRENT USER ====================

@router.get("/me", response_model=UserResponse)
async def read_users_me(current_user: dict = Depends(get_current_user), supabase: Client = Depends(get_supabase)):
    """Get current authenticated user (combines login and profile)."""
    # current_user passed from middleware is just the login data or a minimal set
    # We must fetch the full profile to satisfy UserResponse
    
    user_id = current_user.get("id")
    if not user_id:
         # Fallback if middleware only returns partial
         response = supabase.table("users_login").select("*").eq("email", current_user["email"]).execute()
         if not response.data:
             raise HTTPException(status_code=404, detail="User not found")
         current_user = response.data[0]
         user_id = current_user["id"]

    profile_res = supabase.table("users_profile_login").select("*").eq("user_id", user_id).execute()
    user_profile = profile_res.data[0] if profile_res.data else {}
    
    combined = {**current_user, **user_profile}
    
    return combined
