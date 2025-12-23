"""
Auth Repository
Database access layer for authentication operations.
Handles all Supabase queries and database state management.
"""
from typing import Tuple, Optional
from datetime import datetime
from src.core.database import get_supabase
from src.modules.auth.constants import (
    TABLE_USERS_LOGIN, 
    TABLE_USERS_PROFILE,
    TABLE_USER_OTPS
)
from src.modules.auth.utils import hash_password, hash_otp


class UserRepository:
    """Repository for user table operations."""
    
    @staticmethod
    def get_by_email(email: str) -> Optional[dict]:
        """Get user by email."""
        try:
            supabase = get_supabase()
            response = supabase.table(TABLE_USERS_LOGIN).select("*").eq("email", email).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            print(f"Error getting user by email: {e}")
            return None
    
    @staticmethod
    def get_by_id(user_id: str) -> Optional[dict]:
        """Get user by ID."""
        try:
            supabase = get_supabase()
            response = supabase.table(TABLE_USERS_LOGIN).select("*").eq("id", user_id).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            print(f"Error getting user by ID: {e}")
            return None
    
    @staticmethod
    def exists(email: str) -> bool:
        """Check if user exists by email."""
        return UserRepository.get_by_email(email) is not None
    
    @staticmethod
    def create(user_data: dict) -> Optional[dict]:
        """Create new user."""
        try:
            supabase = get_supabase()
            response = supabase.table(TABLE_USERS_LOGIN).insert(user_data).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            print(f"Error creating user: {e}")
            return None
    
    @staticmethod
    def update(user_id: str, update_data: dict) -> Optional[dict]:
        """Update user record."""
        try:
            supabase = get_supabase()
            response = supabase.table(TABLE_USERS_LOGIN).update(update_data).eq("id", user_id).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            print(f"Error updating user: {e}")
            return None
    
    @staticmethod
    def update_by_email(email: str, update_data: dict) -> Optional[dict]:
        """Update user by email."""
        try:
            supabase = get_supabase()
            response = supabase.table(TABLE_USERS_LOGIN).update(update_data).eq("email", email).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            print(f"Error updating user by email: {e}")
            return None
    
    @staticmethod
    def update_password(email: str, new_password: str) -> bool:
        """Update user password."""
        try:
            hashed_password = hash_password(new_password)
            return UserRepository.update_by_email(email, {"password": hashed_password}) is not None
        except Exception as e:
            print(f"Error updating password: {e}")
            return False


class UserProfileRepository:
    """Repository for user_profile_login table operations."""
    
    @staticmethod
    def get_by_user_id(user_id: str) -> Optional[dict]:
        """Get profile by user ID."""
        try:
            supabase = get_supabase()
            response = supabase.table(TABLE_USERS_PROFILE).select("*").eq("user_id", user_id).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            print(f"Error getting profile: {e}")
            return None
    
    @staticmethod
    def create(profile_data: dict) -> Optional[dict]:
        """Create new profile."""
        try:
            supabase = get_supabase()
            response = supabase.table(TABLE_USERS_PROFILE).insert(profile_data).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            print(f"Error creating profile: {e}")
            return None
    
    @staticmethod
    def update(user_id: str, update_data: dict) -> Optional[dict]:
        """Update profile by user ID."""
        try:
            supabase = get_supabase()
            response = supabase.table(TABLE_USERS_PROFILE).update(update_data).eq("user_id", user_id).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            print(f"Error updating profile: {e}")
            return None
    
    @staticmethod
    def upsert(user_id: str, profile_data: dict) -> Optional[dict]:
        """Create or update profile."""
        existing = UserProfileRepository.get_by_user_id(user_id)
        if existing:
            return UserProfileRepository.update(user_id, profile_data)
        else:
            profile_data["user_id"] = user_id
            return UserProfileRepository.create(profile_data)


class PasswordResetRepository:
    """Repository for password reset OTP operations."""
    
    @staticmethod
    def store_reset_otp(email: str, hashed_otp: str, expiry: datetime) -> bool:
        """Store hashed OTP in profile."""
        try:
            # Get user ID
            user = UserRepository.get_by_email(email)
            if not user:
                return False
            
            user_id = user["id"]
            
            # Check if profile exists
            profile = UserProfileRepository.get_by_user_id(user_id)
            if profile:
                UserProfileRepository.update(user_id, {
                    "reset_otp": hashed_otp,
                    "reset_otp_expiry": expiry.isoformat()
                })
            else:
                UserProfileRepository.create({
                    "user_id": user_id,
                    "reset_otp": hashed_otp,
                    "reset_otp_expiry": expiry.isoformat()
                })
            
            return True
        except Exception as e:
            print(f"Error storing reset OTP: {e}")
            return False
    
    @staticmethod
    def get_reset_otp(email: str) -> Tuple[Optional[str], Optional[str]]:
        """Get stored OTP hash and expiry."""
        try:
            user = UserRepository.get_by_email(email)
            if not user:
                return None, None
            
            profile = UserProfileRepository.get_by_user_id(user["id"])
            if profile:
                return profile.get("reset_otp"), profile.get("reset_otp_expiry")
            return None, None
        except Exception as e:
            print(f"Error getting reset OTP: {e}")
            return None, None
    
    @staticmethod
    def invalidate_reset_otp(email: str) -> bool:
        """Clear reset OTP."""
        try:
            user = UserRepository.get_by_email(email)
            if not user:
                return False
            
            UserProfileRepository.update(user["id"], {
                "reset_otp": None,
                "reset_otp_expiry": None
            })
            return True
        except Exception as e:
            print(f"Error invalidating reset OTP: {e}")
            return False


class EmailVerificationRepository:
    """Repository for email verification token operations."""
    
    @staticmethod
    def store_verification_token(email: str, hashed_token: str, expiry: datetime) -> bool:
        """Store email verification token."""
        try:
            return UserRepository.update_by_email(email, {
                "email_verification_token": hashed_token,
                "email_verification_token_expiry": expiry.isoformat(),
                "email_last_verification_sent_at": datetime.utcnow().isoformat()
            }) is not None
        except Exception as e:
            print(f"Error storing verification token: {e}")
            return False
    
    @staticmethod
    def get_verification_token(email: str) -> Tuple[Optional[str], Optional[str]]:
        """Get stored verification token and expiry."""
        try:
            user = UserRepository.get_by_email(email)
            if user:
                return user.get("email_verification_token"), user.get("email_verification_token_expiry")
            return None, None
        except Exception as e:
            print(f"Error getting verification token: {e}")
            return None, None
    
    @staticmethod
    def mark_email_verified(email: str) -> bool:
        """Mark email as verified and clear token."""
        try:
            return UserRepository.update_by_email(email, {
                "email_verified": True,
                "email_verification_token": None,
                "email_verification_token_expiry": None
            }) is not None
        except Exception as e:
            print(f"Error marking email verified: {e}")
            return False


class OTPRepository:
    """Repository for SMS OTP operations."""
    
    @staticmethod
    def update_phone_verification(phone_number: str) -> bool:
        """Mark phone as verified."""
        try:
            supabase = get_supabase()
            response = supabase.table(TABLE_USERS_LOGIN).update({
                "phone_verification": True,
                "phone_number": phone_number
            }).eq("phone_number", phone_number).execute()
            return response.data is not None
        except Exception as e:
            print(f"Error updating phone verification: {e}")
            return False
