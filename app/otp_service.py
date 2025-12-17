import random
import string
from datetime import datetime, timedelta, timezone
from app.database import get_supabase
from app.twilio_client import get_twilio_client

class OTPService:
    """Service for OTP generation, storage, and verification"""
    
    OTP_LENGTH = 6
    OTP_EXPIRY_MINUTES = 5
    MAX_ATTEMPTS = 3
    
    @staticmethod
    def generate_otp() -> str:
        """Generate a 6-digit OTP code"""
        return ''.join(random.choices(string.digits, k=OTPService.OTP_LENGTH))
    
    @staticmethod
    async def send_otp(phone_number: str) -> dict:
        print(f"DEBUG: send_otp called with phone_number={phone_number}")
        """
        Generate and send OTP to phone number
        
        Args:
            phone_number: Phone number in E.164 format
            
        Returns:
            dict with success status and message
        """
        try:
            supabase = get_supabase()
            
            # Generate OTP
            otp_code = OTPService.generate_otp()
            expires_at = datetime.utcnow() + timedelta(minutes=OTPService.OTP_EXPIRY_MINUTES)
            
            # Store OTP in database
            otp_data = {
                "phone": phone_number,
                "otp": otp_code,
                "expires_at": expires_at.isoformat(),
                "is_used": False
            }
            
            result = supabase.table("user_otps").insert(otp_data).execute()
            
            if not result.data:
                return {"success": False, "message": "Failed to store OTP"}
            
            # Send OTP via Twilio
            twilio = get_twilio_client()
            sms_sent = twilio.send_otp(phone_number, otp_code)
            
            if not sms_sent:
                return {"success": False, "message": "Failed to send SMS"}
            
            return {
                "success": True,
                "message": "OTP sent successfully",
                "expires_at": expires_at.isoformat()
            }
            
        except Exception as e:
            print(f"Error sending OTP: {str(e)}")
            return {"success": False, "message": f"Error: {str(e)}"}
    
    @staticmethod
    async def verify_otp(phone_number: str, otp_code: str) -> dict:
        print(f"DEBUG: verify_otp called with phone_number={phone_number}, otp_code={otp_code}")
        """
        Verify OTP code for phone number
        
        Args:
            phone_number: Phone number in E.164 format
            otp_code: 6-digit OTP code to verify
            
        Returns:
            dict with success status and message
        """
        try:
            supabase = get_supabase()
            
            # Get the most recent unused OTP for this phone number
            result = supabase.table("user_otps")\
                .select("*")\
                .eq("phone", phone_number)\
                .eq("is_used", False)\
                .order("created_at", desc=True)\
                .limit(1)\
                .execute()
            
            if not result.data:
                return {"success": False, "message": "No OTP found for this phone number"}
            
            otp_record = result.data[0]
            print(f"DEBUG: OTP Record: {otp_record}")
            print(f"DEBUG: Raw expires_at: {otp_record['expires_at']}")
            print(f"DEBUG: OTP Code from DB: {otp_record['otp']}")
            print(f"DEBUG: OTP Code from user: {otp_code}")
            
            # Check if OTP has expired - robust timezone‑aware handling
            expires_at_raw = otp_record["expires_at"]
            try:
                # Supabase returns ISO‑8601 strings, possibly with timezone info
                expires_at = datetime.fromisoformat(expires_at_raw)
                if expires_at.tzinfo is None:
                    # Assume UTC if no tz info
                    expires_at = expires_at.replace(tzinfo=timezone.utc)
            except Exception as e:
                print(f"DEBUG: Failed to parse expires_at '{expires_at_raw}': {e}")
                return {"success": False, "message": "Invalid expiration timestamp."}

            now = datetime.now(timezone.utc)

            print(f"DEBUG: Current UTC time: {now.isoformat()}")
            print(f"DEBUG: OTP expires at: {expires_at.isoformat()}")
            remaining = (expires_at - now).total_seconds()
            print(f"DEBUG: Seconds remaining: {remaining}")

            if now > expires_at:
                print("DEBUG: OTP has expired")
                return {"success": False, "message": "OTP has expired. Please request a new one."}
            
            # Verify OTP code
            if otp_record["otp"] != otp_code:
                print("DEBUG: OTP code mismatch")
                return {"success": False, "message": "Invalid OTP code"}
            
            print("DEBUG: OTP verified successfully!")
            
            # Mark OTP as used
            supabase.table("user_otps")\
                .update({"is_used": True})\
                .eq("id", otp_record["id"])\
                .execute()
            
            return {
                "success": True,
                "message": "OTP verified successfully"
            }
            
        except Exception as e:
            print(f"Error verifying OTP: {str(e)}")
            return {"success": False, "message": f"Error: {str(e)}"}
    
    @staticmethod
    async def cleanup_expired_otps():
        """Delete expired OTPs from database (cleanup task)"""
        try:
            supabase = get_supabase()
            now = datetime.utcnow().isoformat()
            
            supabase.table("user_otps")\
                .delete()\
                .lt("expires_at", now)\
                .execute()
            
            print("Cleaned up expired OTPs")
        except Exception as e:
            print(f"Error cleaning up OTPs: {str(e)}")
