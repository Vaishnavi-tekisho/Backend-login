from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.responses import RedirectResponse
from app import schemas, utils, config
from app.database import get_supabase, Client
from app.middleware import get_current_user
from app.otp_service import OTPService
import httpx
from datetime import datetime

router = APIRouter(prefix="/auth", tags=["Authentication"])

from pydantic import BaseModel

@router.post("/signup", response_model=schemas.AuthResponse)
async def register(user_in: schemas.UserCreate, request: Request, supabase: Client = Depends(get_supabase)):
    """
    Register a new user.
    """
    try:
        # 1. Check if user already exists
        # supabase.table('users').select("*").eq('email', email).execute()
        existing = supabase.table("users_login").select("id").eq("email", user_in.email).execute()
        if existing.data:
            raise HTTPException(status_code=400, detail="Email already registered")

        # 2. Hash password
        hashed_pw = utils.get_password_hash(user_in.password)
        
        # 3. Create User object (Dictionary for Supabase)
        user_data = {
            "email": user_in.email,
            "password": hashed_pw,
            "user_name": user_in.user_name,
            "phone_number": user_in.phone_number,
            "location": user_in.location,
            "oauth_provider": "email",
            "ip_address": request.client.host
        }
        
        # 4. Save to DB
        print(f"DEBUG: Attempting to insert user: {user_data['email']}")
        data = supabase.table("users_login").insert(user_data).execute()
        print(f"DEBUG: Supabase Insert Response: {data}")
        
        # data.data is a list of inserted rows
        if not data.data:
             print("Error: No data returned from insert. Check RLS policies.")
             # Check if we are potentially using Anon Key instead of Service Role
             # print(f"DEBUG: Used Key: {supabase.supabase_key}") # Careful not to log secrets in prod
             raise HTTPException(status_code=500, detail="Failed to create user - No data returned (Check RLS Policies)")
        
        user = data.data[0]
        access_token = utils.create_access_token(data={"sub": user["email"]})
        
        return {
            "access_token": access_token, 
            "token_type": "bearer",
            "user": user
        }
    except Exception as e:
        print(f"Exception during registration: {str(e)}")
        # If it's already an HTTPException, re-raise it
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=f"Internal Error: {str(e)}")

@router.post("/login", response_model=schemas.AuthResponse)
async def login(user_in: schemas.UserLogin, supabase: Client = Depends(get_supabase)):
    """
    Login with email and password.
    """
    # 1. Get user
    response = supabase.table("users_login").select("*").eq("email", user_in.email).execute()
    user = response.data[0] if response.data else None
    
    # 2. Verify
    if not user or not user.get("password") or not utils.verify_password(user_in.password, user["password"]):
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
        pass # Don't fail login on stats error

    # 4. Token
    access_token = utils.create_access_token(data={"sub": user["email"]})
    return {
        "access_token": access_token, 
        "token_type": "bearer",
        "user": user
    }

class GoogleTokenRequest(BaseModel):
    token: str

@router.get("/google")
async def login_google():
    return RedirectResponse(
        url=f"https://accounts.google.com/o/oauth2/auth?response_type=code&client_id={config.settings.GOOGLE_CLIENT_ID}&redirect_uri={config.settings.GOOGLE_REDIRECT_URI}&scope=openid%20profile%20email&access_type=offline"
    )

@router.get("/callback")
async def auth_google_callback(code: str, request: Request, supabase: Client = Depends(get_supabase)):
    try:
        print(f"DEBUG: Received callback with code: {code[:20]}...")
        
        token_url = "https://accounts.google.com/o/oauth2/token"
        data = {
            "code": code,
            "client_id": config.settings.GOOGLE_CLIENT_ID,
            "client_secret": config.settings.GOOGLE_CLIENT_SECRET,
            "redirect_uri": config.settings.GOOGLE_REDIRECT_URI,
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
        # Trigger verification logic
        token_req = GoogleTokenRequest(token=access_token_info["id_token"])
        
        print("DEBUG: Calling google_verify")
        # We call the verify function directly. Note: verify function returns a dict.
        auth_result = await google_verify(token_req, request, supabase)
        
        print(f"DEBUG: Verification successful, user: {auth_result['user'].get('email')}")
        
        # Redirect to frontend with token and user data
        frontend_url = "http://localhost:5173/oauth-success"
        
        import json
        import urllib.parse
        
        user_json = json.dumps(auth_result['user'])
        user_encoded = urllib.parse.quote(user_json)
        
        redirect_url = f"{frontend_url}?token={auth_result['access_token']}&user={user_encoded}"
        print(f"DEBUG: Redirecting to: {redirect_url[:100]}...")
        
        return RedirectResponse(url=redirect_url)
    
    except HTTPException as he:
        print(f"HTTP Exception in callback: {he.detail}")
        raise he
    except Exception as e:
        print(f"ERROR in Google OAuth callback: {str(e)}")
        print(f"ERROR type: {type(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Internal error during OAuth: {str(e)}")

@router.post("/google", response_model=schemas.AuthResponse)
async def google_login(token_req: GoogleTokenRequest, request: Request, supabase: Client = Depends(get_supabase)):
    """
    Verify Google Token and login/register user.
    """
    return await google_verify(token_req, request, supabase)

@router.post("/google-verify", response_model=schemas.AuthResponse) 
async def google_verify(token_req: GoogleTokenRequest, request: Request, supabase: Client = Depends(get_supabase)):
    token = token_req.token
    
    async with httpx.AsyncClient() as client:
        resp = await client.get(f"https://oauth2.googleapis.com/tokeninfo?id_token={token}")
        
    if resp.status_code != 200:
        raise HTTPException(status_code=401, detail="Invalid Google Token")
        
    payload = resp.json()
    if config.settings.GOOGLE_CLIENT_ID and payload.get("aud") != config.settings.GOOGLE_CLIENT_ID:
         raise HTTPException(status_code=401, detail="Invalid Client ID in Token")

    email = payload.get("email")
    response = supabase.table("users_login").select("*").eq("email", email).execute()
    user = response.data[0] if response.data else None
    
    if not user:
        # Register
        new_user = {
            "email": email,
            "user_name": payload.get("name"),
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

    access_token = utils.create_access_token(data={"sub": user["email"]})
    return {
        "access_token": access_token, 
        "token_type": "bearer",
        "user": user
    }

@router.get("/me", response_model=schemas.UserResponse)
async def read_users_me(current_user: dict = Depends(get_current_user)):
    return current_user

@router.post("/request-password-reset")
async def request_password_reset(request: schemas.ForgotPasswordRequest, supabase: Client = Depends(get_supabase)):
    """
    Request a password reset OTP via email.
    """
    email = request.email
    
    # 1. Check if user exists
    response = supabase.table("users_login").select("id").eq("email", email).execute()
    
    if not response.data:
        raise HTTPException(
            status_code=404, 
            detail="Account not found. Please create an account first."
        )

    # 2. Generate 6-digit OTP
    otp = OTPService.generate_otp()
    
    # 3. Hash the OTP before storing (for security)
    hashed_otp = utils.get_password_hash(otp)
    
    # 4. Store hashed OTP in database with expiry (5 minutes)
    from datetime import datetime, timedelta
    otp_expiry = (datetime.utcnow() + timedelta(minutes=5)).isoformat()
    
    # Update user record with hashed OTP and expiry
    supabase.table("users_login").update({
        "reset_otp": hashed_otp,
        "reset_otp_expiry": otp_expiry
    }).eq("email", email).execute()

    # 5. Send OTP via email using SendGrid dynamic template
    try:
        utils.send_otp_email(
            to_email=email,
            otp=otp,
            app_name="LeadQ"
        )
        
        return {"message": "OTP has been sent to your email.", "success": True}
    except Exception as e:
        print(f"Error sending OTP email: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to send OTP email")

@router.post("/verify-reset-otp")
async def verify_reset_otp(request: schemas.VerifyResetOTPRequest, supabase: Client = Depends(get_supabase)):
    """
    Verify the password reset OTP.
    """
    from datetime import datetime
    
    email = request.email
    otp = request.otp
    
    # 1. Get user's stored hashed OTP and expiry
    response = supabase.table("users_login").select("reset_otp, reset_otp_expiry").eq("email", email).execute()
    
    if not response.data:
        raise HTTPException(status_code=404, detail="User not found")
    
    user_data = response.data[0]
    stored_hashed_otp = user_data.get("reset_otp")
    otp_expiry = user_data.get("reset_otp_expiry")
    
    if not stored_hashed_otp or not otp_expiry:
        raise HTTPException(status_code=400, detail="No OTP request found. Please request a new OTP.")
    
    # 2. Check if OTP has expired
    expiry_time = datetime.fromisoformat(otp_expiry.replace('Z', '+00:00'))
    if datetime.utcnow() > expiry_time.replace(tzinfo=None):
        raise HTTPException(status_code=400, detail="OTP has expired. Please request a new OTP.")
    
    # 3. Verify OTP by comparing with hashed value
    if not utils.verify_password(otp, stored_hashed_otp):
        raise HTTPException(status_code=400, detail="Invalid OTP")
    
    return {"message": "OTP verified successfully", "success": True}

@router.post("/reset-password-with-otp")
async def reset_password_with_otp(request: schemas.ResetPasswordWithOTPRequest, supabase: Client = Depends(get_supabase)):
    """
    Reset password after OTP verification.
    """
    from datetime import datetime
    
    email = request.email
    otp = request.otp
    new_password = request.new_password
    
    # 1. Get user's stored hashed OTP and expiry
    response = supabase.table("users_login").select("reset_otp, reset_otp_expiry").eq("email", email).execute()
    
    if not response.data:
        raise HTTPException(status_code=404, detail="User not found")
    
    user_data = response.data[0]
    stored_hashed_otp = user_data.get("reset_otp")
    otp_expiry = user_data.get("reset_otp_expiry")
    
    if not stored_hashed_otp or not otp_expiry:
        raise HTTPException(status_code=400, detail="No OTP request found. Please request a new OTP.")
    
    # 2. Check if OTP has expired
    expiry_time = datetime.fromisoformat(otp_expiry.replace('Z', '+00:00'))
    if datetime.utcnow() > expiry_time.replace(tzinfo=None):
        raise HTTPException(status_code=400, detail="OTP has expired. Please request a new OTP.")
    
    # 3. Verify OTP
    if not utils.verify_password(otp, stored_hashed_otp):
        raise HTTPException(status_code=400, detail="Invalid OTP")
    
    # 4. Update password
    hashed_password = utils.get_password_hash(new_password)
    supabase.table("users_login").update({
        "password": hashed_password,
        "reset_otp": None,
        "reset_otp_expiry": None
    }).eq("email", email).execute()
    
    return {"message": "Password reset successfully", "success": True}

@router.post("/reset-password")
async def reset_password_confirm(request: schemas.ResetPasswordConfirm, supabase: Client = Depends(get_supabase)):
    """
    Complete password reset: Update password in Supabase and local DB.
    """
    token = request.supabase_access_token
    new_password = request.new_password
    
    try:
        # 1. Verify Token & Get User
        user_response = supabase.auth.get_user(token)
        if not user_response or not user_response.user:
             raise HTTPException(status_code=401, detail="Invalid or expired reset token")
             
        user_id = user_response.user.id
        email = user_response.user.email
        
        # 2. Update Supabase Auth Password
        # Since we initialized supabase with Service Role Key (in database.py), we can use admin api
        # or we could use the token. Using admin is robust.
        supabase.auth.admin.update_user_by_id(user_id, {"password": new_password})
        
        # 3. Update Local DB Password (to keep sync)
        hashed_pw = utils.get_password_hash(new_password)
        
        data = supabase.table("users_login").update({
            "password": hashed_pw,
            "last_login": datetime.utcnow().isoformat()
        }).eq("email", email).execute()
        
        return {"message": "Password updated successfully"}
        
    except Exception as e:
        print(f"Error resetting password: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

# OTP Endpoints
# OTP Endpoints
@router.post("/send-otp", response_model=schemas.OTPResponse)
async def send_otp(request: schemas.SendOTPRequest):
    """
    Send OTP to phone number for verification using Twilio Verify
    """
    try:
        from twilio.rest import Client
        import os
        
        # Load credentials newly to ensure they are picked up
        account_sid = config.settings.TWILIO_ACCOUNT_SID
        auth_token = config.settings.TWILIO_AUTH_TOKEN
        # Check both config paths for service sid
        verify_service_sid = config.settings.TWILIO_VERIFY_SERVICE_SID
        
        if not account_sid or not auth_token or not verify_service_sid:
             print(f"DEBUG: Missing Twilio Config. SID: {bool(account_sid)}, Token: {bool(auth_token)}, Service: {bool(verify_service_sid)}")
             return {"success": False, "message": "Server Config Error: Missing Twilio Credentials"}

        client = Client(account_sid, auth_token)
        
        verification = client.verify.v2.services(verify_service_sid) \
            .verifications \
            .create(to=request.phone_number, channel='sms')
        
        print(f"DEBUG: Twilio Send Response: {verification.status}")
        return {"success": True, "message": "OTP sent successfully"}
    except Exception as e:
        print(f"DEBUG: Twilio Send Error: {str(e)}")
        # Check for specific Twilio errors if needed
        return {"success": False, "message": str(e)}


@router.post("/verify-otp", response_model=schemas.OTPResponse)
async def verify_otp(request: schemas.VerifyOTPRequest):
    """
    Verify OTP code for phone number using Twilio Verify
    """
    try:
        from twilio.rest import Client
        import os
        
        account_sid = config.settings.TWILIO_ACCOUNT_SID
        auth_token = config.settings.TWILIO_AUTH_TOKEN
        verify_service_sid = config.settings.TWILIO_VERIFY_SERVICE_SID
        
        client = Client(account_sid, auth_token)

        verification_check = client.verify.v2.services(verify_service_sid) \
            .verification_checks \
            .create(to=request.phone_number, code=request.otp_code)
        
        print(f"DEBUG: Twilio Verify Status: {verification_check.status}")
        
        if verification_check.status == "approved":
            return {"success": True, "message": "OTP Verified"}
        else:
            return {"success": False, "message": "Invalid OTP"}
            
    except Exception as e:
        print(f"DEBUG: Twilio Verify Error: {str(e)}")
        return {"success": False, "message": str(e)}

# Note: Password reset endpoints have been moved to app/password_routes/password_reset.py
# The new endpoints are:
# POST /auth/forgot-password - Request password reset OTP
# POST /auth/verify-reset-otp - Verify the OTP
# POST /auth/reset-password - Reset password with verified OTP




