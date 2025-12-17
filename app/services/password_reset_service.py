"""
Password Reset Service
Handles OTP generation, storage, verification, and password reset logic.
Isolated from login OTP logic.
"""
import random
import string
from datetime import datetime, timedelta
from typing import Tuple, Optional
from passlib.context import CryptContext

from app.db.supabase_client import get_supabase
from app.services.email_service import EmailService


# Use bcrypt for OTP hashing (same as password hashing)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class PasswordResetService:
    """
    Service for password reset OTP operations.
    Separate from phone/login OTP to maintain single responsibility.
    """
    
    OTP_LENGTH = 6
    OTP_EXPIRY_MINUTES = 5
    
    @staticmethod
    def generate_otp() -> str:
        """Generate a 6-digit numeric OTP."""
        return ''.join(random.choices(string.digits, k=PasswordResetService.OTP_LENGTH))
    
    @staticmethod
    def hash_otp(otp: str) -> str:
        """Hash OTP using bcrypt before storage."""
        return pwd_context.hash(otp)
    
    @staticmethod
    def verify_otp_hash(plain_otp: str, hashed_otp: str) -> bool:
        """Verify plain OTP against hashed OTP."""
        return pwd_context.verify(plain_otp, hashed_otp)
    
    @staticmethod
    def get_expiry_time() -> datetime:
        """Get OTP expiry timestamp (5 minutes from now)."""
        return datetime.utcnow() + timedelta(minutes=PasswordResetService.OTP_EXPIRY_MINUTES)
    
    @staticmethod
    def is_expired(expiry_str: str) -> bool:
        """Check if OTP has expired."""
        try:
            # Handle different datetime formats
            expiry_str_clean = expiry_str.replace('Z', '+00:00')
            if '+' in expiry_str_clean:
                expiry_time = datetime.fromisoformat(expiry_str_clean).replace(tzinfo=None)
            else:
                expiry_time = datetime.fromisoformat(expiry_str_clean)
            return datetime.utcnow() > expiry_time
        except Exception as e:
            print(f"Error parsing expiry time: {e}")
            return True  # Treat as expired if parsing fails

    @staticmethod
    def check_user_exists(email: str) -> Tuple[bool, Optional[dict]]:
        """
        Check if user exists in database.
        
        Returns:
            Tuple of (exists: bool, user_data: dict or None)
        """
        try:
            supabase = get_supabase()
            response = supabase.table("users_login").select("id, email").eq("email", email).execute()
            
            if response.data and len(response.data) > 0:
                return True, response.data[0]
            return False, None
        except Exception as e:
            print(f"Error checking user existence: {e}")
            return False, None

    @staticmethod
    def store_reset_otp(email: str, hashed_otp: str, expiry: datetime) -> bool:
        """
        Store hashed OTP and expiry in user record.
        
        Args:
            email: User email
            hashed_otp: Bcrypt hashed OTP
            expiry: Expiry datetime
            
        Returns:
            bool: True if stored successfully
        """
        try:
            supabase = get_supabase()
            print(f"DEBUG: Attempting to store OTP for {email}")
            result = supabase.table("users_login").update({
                "reset_otp": hashed_otp,
                "reset_otp_expiry": expiry.isoformat()
            }).eq("email", email).execute()
            
            print(f"DEBUG: Supabase update result: {result}")
            return result.data is not None and len(result.data) > 0
        except Exception as e:
            print(f"Error storing reset OTP: {e}")
            return False

    @staticmethod
    def get_stored_otp(email: str) -> Tuple[Optional[str], Optional[str]]:
        """
        Get stored OTP hash and expiry for user.
        
        Returns:
            Tuple of (hashed_otp, expiry_str) or (None, None)
        """
        try:
            supabase = get_supabase()
            response = supabase.table("users_login").select(
                "reset_otp, reset_otp_expiry"
            ).eq("email", email).execute()
            
            if response.data and len(response.data) > 0:
                user = response.data[0]
                return user.get("reset_otp"), user.get("reset_otp_expiry")
            return None, None
        except Exception as e:
            print(f"Error getting stored OTP: {e}")
            return None, None

    @staticmethod
    def invalidate_otp(email: str) -> bool:
        """
        Invalidate OTP after use (set to NULL).
        
        Args:
            email: User email
            
        Returns:
            bool: True if invalidated successfully
        """
        try:
            supabase = get_supabase()
            result = supabase.table("users_login").update({
                "reset_otp": None,
                "reset_otp_expiry": None
            }).eq("email", email).execute()
            
            return result.data is not None
        except Exception as e:
            print(f"Error invalidating OTP: {e}")
            return False

    @staticmethod
    def update_password(email: str, new_password: str) -> bool:
        """
        Update user password in database.
        
        Args:
            email: User email
            new_password: New plain text password (will be hashed)
            
        Returns:
            bool: True if password updated successfully
        """
        try:
            supabase = get_supabase()
            hashed_password = pwd_context.hash(new_password)
            
            result = supabase.table("users_login").update({
                "password": hashed_password,
                "reset_otp": None,  # Invalidate OTP
                "reset_otp_expiry": None
            }).eq("email", email).execute()
            
            return result.data is not None and len(result.data) > 0
        except Exception as e:
            print(f"Error updating password: {e}")
            return False

    # ==================== HIGH-LEVEL SERVICE METHODS ====================

    @classmethod
    def request_password_reset(cls, email: str) -> dict:
        """
        Handle forgot password request:
        1. Check if user exists
        2. Generate OTP
        3. Hash and store OTP
        4. Send OTP via email
        
        Args:
            email: User email address
            
        Returns:
            dict with success status and message
        """
        print(f"DEBUG: Password reset requested for: {email}")
        
        # 1. Check if user exists
        exists, user = cls.check_user_exists(email)
        print(f"DEBUG: User exists: {exists}")
        if not exists:
            return {
                "success": False,
                "error": "Account not found. Please create an account first."
            }
        
        # 2. Generate OTP
        otp = cls.generate_otp()
        print(f"DEBUG: Generated OTP: {otp}")
        
        # 3. Hash OTP and calculate expiry
        hashed_otp = cls.hash_otp(otp)
        expiry = cls.get_expiry_time()
        
        # 4. Store hashed OTP in database
        store_result = cls.store_reset_otp(email, hashed_otp, expiry)
        print(f"DEBUG: Store OTP result: {store_result}")
        if not store_result:
            return {
                "success": False,
                "error": "Failed to process request. Please try again."
            }
        
        # 5. Send OTP via email (plain OTP, not hashed)
        print(f"DEBUG: Sending OTP email to {email}")
        email_result = EmailService.send_password_reset_otp(email, otp)
        print(f"DEBUG: Email send result: {email_result}")
        if not email_result:
            return {
                "success": False,
                "error": "Failed to send OTP email. Please try again."
            }
        
        return {
            "success": True,
            "message": "OTP has been sent to your email."
        }

    @classmethod
    def verify_reset_otp(cls, email: str, otp: str) -> dict:
        """
        Verify password reset OTP:
        1. Get stored OTP hash and expiry
        2. Check expiry
        3. Verify OTP hash
        
        Note: Does NOT invalidate OTP - that happens during password reset
        
        Args:
            email: User email
            otp: Plain text OTP from user
            
        Returns:
            dict with success status and message
        """
        # 1. Get stored OTP data
        stored_hash, expiry_str = cls.get_stored_otp(email)
        
        if not stored_hash or not expiry_str:
            return {
                "success": False,
                "error": "No OTP request found. Please request a new OTP."
            }
        
        # 2. Check if OTP has expired
        if cls.is_expired(expiry_str):
            # Invalidate expired OTP
            cls.invalidate_otp(email)
            return {
                "success": False,
                "error": "OTP has expired. Please request a new OTP."
            }
        
        # 3. Verify OTP hash
        if not cls.verify_otp_hash(otp, stored_hash):
            return {
                "success": False,
                "error": "Invalid OTP. Please check and try again."
            }
        
        return {
            "success": True,
            "message": "OTP verified successfully."
        }

    @classmethod
    def reset_password(cls, email: str, otp: str, new_password: str) -> dict:
        """
        Reset password after OTP verification:
        1. Verify OTP again (security)
        2. Update password
        3. Invalidate OTP (single-use)
        
        Args:
            email: User email
            otp: Plain text OTP
            new_password: New password
            
        Returns:
            dict with success status and message
        """
        # 1. Verify OTP first
        verification = cls.verify_reset_otp(email, otp)
        if not verification["success"]:
            return verification
        
        # 2. Update password (also invalidates OTP)
        if not cls.update_password(email, new_password):
            return {
                "success": False,
                "error": "Failed to update password. Please try again."
            }
        
        return {
            "success": True,
            "message": "Password reset successfully. You can now login with your new password."
        }
