"""
OTP Service
Handles SMS OTP operations via Twilio.
"""
import random
import string
from datetime import datetime, timedelta
from typing import Dict, Any

from app.db.supabase_client import get_supabase
from app.core.config import settings


class OTPService:
    """Service for SMS OTP operations via Twilio."""
    
    OTP_LENGTH = 6
    OTP_EXPIRY_MINUTES = 5
    
    @staticmethod
    def generate_otp() -> str:
        """Generate a 6-digit OTP code."""
        return ''.join(random.choices(string.digits, k=OTPService.OTP_LENGTH))
    
    @staticmethod
    async def send_otp(phone_number: str) -> Dict[str, Any]:
        """
        Generate and send OTP to phone number via Twilio Verify.
        
        Args:
            phone_number: Phone number in E.164 format
            
        Returns:
            dict with success status and message
        """
        print(f"DEBUG: send_otp called with phone_number={phone_number}")
        
        try:
            from twilio.rest import Client
            
            account_sid = settings.TWILIO_ACCOUNT_SID
            auth_token = settings.TWILIO_AUTH_TOKEN
            verify_service_sid = settings.TWILIO_VERIFY_SERVICE_SID
            
            if not account_sid or not auth_token or not verify_service_sid:
                return {"success": False, "message": "Missing Twilio credentials"}
            
            client = Client(account_sid, auth_token)
            
            verification = client.verify.v2.services(verify_service_sid) \
                .verifications \
                .create(to=phone_number, channel='sms')
            
            print(f"DEBUG: Twilio Send Response: {verification.status}")
            
            return {
                "success": True,
                "message": "OTP sent successfully",
                "expires_at": (datetime.utcnow() + timedelta(minutes=OTPService.OTP_EXPIRY_MINUTES)).isoformat()
            }
            
        except Exception as e:
            print(f"Error sending OTP: {str(e)}")
            return {"success": False, "message": f"Error: {str(e)}"}
    
    @staticmethod
    async def verify_otp(phone_number: str, otp_code: str) -> Dict[str, Any]:
        """
        Verify OTP code for phone number via Twilio Verify.
        
        Args:
            phone_number: Phone number in E.164 format
            otp_code: 6-digit OTP code to verify
            
        Returns:
            dict with success status and message
        """
        print(f"DEBUG: verify_otp called with phone_number={phone_number}, otp_code={otp_code}")
        
        try:
            from twilio.rest import Client
            
            account_sid = settings.TWILIO_ACCOUNT_SID
            auth_token = settings.TWILIO_AUTH_TOKEN
            verify_service_sid = settings.TWILIO_VERIFY_SERVICE_SID
            
            client = Client(account_sid, auth_token)

            verification_check = client.verify.v2.services(verify_service_sid) \
                .verification_checks \
                .create(to=phone_number, code=otp_code)
            
            print(f"DEBUG: Twilio Verify Status: {verification_check.status}")
            
            if verification_check.status == "approved":
                return {"success": True, "message": "OTP Verified"}
            else:
                return {"success": False, "message": "Invalid OTP"}
                
        except Exception as e:
            print(f"DEBUG: Twilio Verify Error: {str(e)}")
            return {"success": False, "message": str(e)}
