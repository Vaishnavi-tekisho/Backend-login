"""
Verification Service
Handles email verification logic using manual tokens and SendGrid.
"""
from datetime import datetime, timedelta
import secrets
import urllib.parse
from passlib.context import CryptContext

from app.db.supabase_client import get_supabase
from app.services.email_service import EmailService

# Reuse context for consistent hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class VerificationService:
    """
    Service for email verification operations.
    """
    
    COOLDOWN_MINUTES = 2
    
    @staticmethod
    def hash_token(token: str) -> str:
        """Hash token using bcrypt."""
        return pwd_context.hash(token)
    
    @staticmethod
    def verify_token_hash(plain_token: str, hashed_token: str) -> bool:
        """Verify plain token against hashed token."""
        return pwd_context.verify(plain_token, hashed_token)
    
    @classmethod
    def request_verification_email(cls, email: str, redirect_url: str = "http://localhost:5173/login/verification-success") -> dict:
        """
        Generate verification token and send email.
        Now includes a 2-minute cooldown check.
        """
        try:
            supabase = get_supabase()
            
            # 1. Get User
            response = supabase.table("users_login").select(
                "id, email, first_name, last_name, email_verified, email_last_verification_sent_at"
            ).eq("email", email).execute()
            
            if not response.data:
                return {"success": False, "error": "User not found"}
            
            user = response.data[0]
            if user.get("email_verified"):
                return {"success": False, "error": "Email already verified"}

            # 2. Cooldown Check
            last_sent_str = user.get("email_last_verification_sent_at")
            if last_sent_str:
                last_sent = datetime.fromisoformat(last_sent_str.replace('Z', '+00:00')).replace(tzinfo=None)
                wait_time = datetime.utcnow() - last_sent
                if wait_time < timedelta(minutes=cls.COOLDOWN_MINUTES):
                    remaining = int(timedelta(minutes=cls.COOLDOWN_MINUTES).total_seconds() - wait_time.total_seconds())
                    return {
                        "success": False, 
                        "error": f"Please wait {remaining} seconds before requesting another email."
                    }

            # 3. Generate Token
            token = secrets.token_urlsafe(32)
            hashed_token = cls.hash_token(token)
            expiry = (datetime.utcnow() + timedelta(hours=24)).isoformat()
            now = datetime.utcnow().isoformat()
            
            # 4. Store in DB
            store_res = supabase.table("users_login").update({
                "email_verification_token": hashed_token,
                "email_verification_token_expiry": expiry,
                "email_last_verification_sent_at": now
            }).eq("email", email).execute()
            
            if not store_res.data:
                return {"success": False, "error": "Failed to store verification token"}

            # 5. Send Email
            encoded_token = urllib.parse.quote(token)
            encoded_email = urllib.parse.quote(email)
            
            separator = "&" if "?" in redirect_url else "?"
            link = f"{redirect_url}{separator}token={encoded_token}&email={encoded_email}"
            
            user_context = {
                "first_name": user.get("first_name", ""),
                "last_name": user.get("last_name", ""),
                "name": user.get("first_name", "")
            }
            
            res = EmailService.send_verification_email(email, link, user_context)
            
            if res:
                return {"success": True, "message": "Verification email sent"}
            return {"success": False, "error": "Failed to send email. Check SendGrid configuration."}
            
        except Exception as e:
            print(f"Error requesting verification: {e}")
            return {"success": False, "error": f"Internal Error: {str(e)}"}

    @classmethod
    def verify_email(cls, email: str, token: str) -> dict:
        """
        Verify email using token.
        """
        try:
            supabase = get_supabase()
            
            # 1. Get stored token
            response = supabase.table("users_login").select(
                "email_verification_token, email_verification_token_expiry"
            ).eq("email", email).execute()
            
            if not response.data:
                return {"success": False, "error": "User not found"}
            
            user = response.data[0]
            stored_hash = user.get("email_verification_token")
            expiry = user.get("email_verification_token_expiry")
            
            if not stored_hash or not expiry:
                return {"success": False, "error": "No verification request found for this email."}
            
            # 2. Check Expiry
            expiry_date = datetime.fromisoformat(expiry.replace('Z', '+00:00')).replace(tzinfo=None)
            if datetime.utcnow() > expiry_date:
                return {"success": False, "error": "Verification link has expired. Please request a new one."}
            
            # 3. Verify Hash
            if not cls.verify_token_hash(token, stored_hash):
                return {"success": False, "error": "Invalid verification link."}
            
            # 4. Mark verified
            supabase.table("users_login").update({
                "email_verified": True,
                "email_verification_token": None,
                "email_verification_token_expiry": None
            }).eq("email", email).execute()
            
            return {"success": True, "message": "Email verified successfully!"}
            
        except Exception as e:
            print(f"Error verifying email: {e}")
            return {"success": False, "error": f"Internal Error: {str(e)}"}
