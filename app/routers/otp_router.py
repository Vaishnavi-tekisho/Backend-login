"""
OTP Router
Handles SMS OTP operations via Twilio.
"""
from fastapi import APIRouter, Depends
from app.db.supabase_client import get_supabase, get_supabase_admin, Client

from app.core.config import settings
from app.models.otp_model import SendOTPRequest, VerifyOTPRequest, OTPResponse


router = APIRouter(prefix="/auth", tags=["OTP"])


@router.post("/send-otp", response_model=OTPResponse)
async def send_otp(request: SendOTPRequest):
    """
    Send OTP to phone number for verification using Twilio Verify.
    """
    try:
        from twilio.rest import Client
        
        account_sid = settings.TWILIO_ACCOUNT_SID
        auth_token = settings.TWILIO_AUTH_TOKEN
        verify_service_sid = settings.TWILIO_VERIFY_SERVICE_SID
        
        if not account_sid or not auth_token or not verify_service_sid:
            print(f"DEBUG: Missing Twilio Config. SID: {bool(account_sid)}, Token: {bool(auth_token)}, Service: {bool(verify_service_sid)}")
            return OTPResponse(success=False, message="Server Config Error: Missing Twilio Credentials")

        client = Client(account_sid, auth_token)
        
        verification = client.verify.v2.services(verify_service_sid) \
            .verifications \
            .create(to=request.phone_number, channel='sms')
        
        print(f"DEBUG: Twilio Send Response: {verification.status}")
        return OTPResponse(success=True, message="OTP sent successfully")
        
    except Exception as e:
        print(f"DEBUG: Twilio Send Error: {str(e)}")
        return OTPResponse(success=False, message=str(e))


@router.post("/verify-otp", response_model=OTPResponse)
async def verify_otp(request: VerifyOTPRequest, supabase: Client = Depends(get_supabase_admin)):
    """
    Verify OTP code for phone number using Twilio Verify.
    """
    try:
        from twilio.rest import Client
        
        account_sid = settings.TWILIO_ACCOUNT_SID
        auth_token = settings.TWILIO_AUTH_TOKEN
        verify_service_sid = settings.TWILIO_VERIFY_SERVICE_SID
        
        client = Client(account_sid, auth_token)

        verification_check = client.verify.v2.services(verify_service_sid) \
            .verification_checks \
            .create(to=request.phone_number, code=request.otp_code)
        
        print(f"DEBUG: Twilio Verify Status: {verification_check.status}")
        
        if verification_check.status == "approved":
            # Update user phone_verification status
            try:
                # We assume the phone number is unique to a user
                supabase.table("users_login").update({
                    "phone_verification": True,
                    "phone_number": request.phone_number # Ensure it matches
                }).eq("phone_number", request.phone_number).execute()
                print(f"DEBUG: Updated phone verification for {request.phone_number}")
            except Exception as e:
                print(f"WARNING: Failed to update user DB after OTP verify: {e}")

            return OTPResponse(success=True, message="OTP Verified")
        else:
            return OTPResponse(success=False, message="Invalid OTP")
            
    except Exception as e:
        print(f"DEBUG: Twilio Verify Error: {str(e)}")
        return OTPResponse(success=False, message=str(e))
