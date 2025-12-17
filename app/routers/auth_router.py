"""
Authentication Router
Handles signup, login, and OAuth authentication endpoints.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.responses import RedirectResponse
import httpx
from datetime import datetime
import json
import urllib.parse

from app.core.config import settings
from app.core.security import create_access_token, verify_password, get_password_hash
from app.db.supabase_client import get_supabase, Client
from app.models.user_model import (
    UserCreate, 
    UserLogin, 
    GoogleTokenRequest, 
    AuthResponse, 
    UserResponse
)
from app.middleware.auth_middleware import get_current_user


router = APIRouter(prefix="/auth", tags=["Authentication"])


# ==================== SIGNUP ====================

@router.post("/signup", response_model=AuthResponse)
async def register(user_in: UserCreate, request: Request, supabase: Client = Depends(get_supabase)):
    """
    Register a new user with email and password.
    """
    try:
        # 1. Check if user already exists
        existing = supabase.table("users_login").select("id").eq("email", user_in.email).execute()
        if existing.data:
            raise HTTPException(status_code=400, detail="Email already registered")

        # 2. Hash password
        hashed_pw = get_password_hash(user_in.password)
        
        # 3. Create user data
        user_data = {
            "email": user_in.email,
            "password": hashed_pw,
            "first_name": user_in.first_name,
            "last_name": user_in.last_name,
            "phone_number": user_in.phone_number,
            "location": user_in.location,
            "oauth_provider": "email",
            "ip_address": request.client.host
        }
        
        # 4. Save to DB
        print(f"DEBUG: Attempting to insert user: {user_data['email']}")
        data = supabase.table("users_login").insert(user_data).execute()
        print(f"DEBUG: Supabase Insert Response: {data}")
        
        if not data.data:
            print("Error: No data returned from insert. Check RLS policies.")
            raise HTTPException(status_code=500, detail="Failed to create user - No data returned (Check RLS Policies)")
        
        user = data.data[0]
        access_token = create_access_token(data={"sub": user["email"]})
        
        return {
            "access_token": access_token, 
            "token_type": "bearer",
            "user": user
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"Exception during registration: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal Error: {str(e)}")


# ==================== LOGIN ====================

@router.post("/login", response_model=AuthResponse)
async def login(user_in: UserLogin, supabase: Client = Depends(get_supabase)):
    """
    Login with email and password.
    """
    # 1. Get user
    response = supabase.table("users_login").select("*").eq("email", user_in.email).execute()
    user = response.data[0] if response.data else None
    
    # 2. Verify
    if not user or not user.get("password") or not verify_password(user_in.password, user["password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 3. Update stats
    try:
        supabase.table("users_login").update({
            "last_login": datetime.utcnow().isoformat()
        }).eq("id", user["id"]).execute()
    except:
        pass  # Don't fail login on stats error

    # 4. Token
    access_token = create_access_token(data={"sub": user["email"]})
    return {
        "access_token": access_token, 
        "token_type": "bearer",
        "user": user
    }


# ==================== GOOGLE OAUTH ====================

@router.get("/google")
async def login_google():
    """Redirect to Google OAuth consent screen."""
    return RedirectResponse(
        url=f"https://accounts.google.com/o/oauth2/auth?response_type=code&client_id={settings.GOOGLE_CLIENT_ID}&redirect_uri={settings.GOOGLE_REDIRECT_URI}&scope=openid%20profile%20email&access_type=offline"
    )


@router.get("/callback")
async def auth_google_callback(code: str, request: Request, supabase: Client = Depends(get_supabase)):
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
        auth_result = await google_verify(token_req, request, supabase)
        
        print(f"DEBUG: Verification successful, user: {auth_result['user'].get('email')}")
        
        # Redirect to frontend with token and user data
        frontend_url = "http://localhost:5173/oauth-success"
        
        user_json = json.dumps(auth_result['user'])
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
async def google_login(token_req: GoogleTokenRequest, request: Request, supabase: Client = Depends(get_supabase)):
    """Verify Google Token and login/register user."""
    return await google_verify(token_req, request, supabase)


@router.post("/google-verify", response_model=AuthResponse)
async def google_verify(token_req: GoogleTokenRequest, request: Request, supabase: Client = Depends(get_supabase)):
    """Verify Google ID token and create/login user."""
    token = token_req.token
    
    async with httpx.AsyncClient() as client:
        resp = await client.get(f"https://oauth2.googleapis.com/tokeninfo?id_token={token}")
        
    if resp.status_code != 200:
        raise HTTPException(status_code=401, detail="Invalid Google Token")
        
    payload = resp.json()
    if settings.GOOGLE_CLIENT_ID and payload.get("aud") != settings.GOOGLE_CLIENT_ID:
        raise HTTPException(status_code=401, detail="Invalid Client ID in Token")

    email = payload.get("email")
    response = supabase.table("users_login").select("*").eq("email", email).execute()
    user = response.data[0] if response.data else None
    
    if not user:
        # Register new user - split name into first and last
        full_name = payload.get("name", "")
        name_parts = full_name.split(" ", 1) if full_name else ["", ""]
        first_name = name_parts[0] if name_parts else ""
        last_name = name_parts[1] if len(name_parts) > 1 else ""
        
        new_user = {
            "email": email,
            "first_name": first_name,
            "last_name": last_name,
            "profile_image_url": payload.get("picture"),
            "oauth_provider": "google",
            "is_active": True,
            "email_verified": True,
            "ip_address": request.client.host,
            "last_login": datetime.utcnow().isoformat()
        }
        data = supabase.table("users_login").insert(new_user).execute()
        user = data.data[0]
    else:
        supabase.table("users_login").update({
            "last_login": datetime.utcnow().isoformat()
        }).eq("id", user["id"]).execute()

    access_token = create_access_token(data={"sub": user["email"]})
    return {
        "access_token": access_token, 
        "token_type": "bearer",
        "user": user
    }


# ==================== CURRENT USER ====================

@router.get("/me", response_model=UserResponse)
async def read_users_me(current_user: dict = Depends(get_current_user)):
    """Get current authenticated user."""
    return current_user
