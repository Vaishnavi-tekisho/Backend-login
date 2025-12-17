"""
User Service
Business logic for user operations.
"""
from datetime import datetime
from typing import Optional, Dict, Any

from app.db.supabase_client import get_supabase
from app.core.security import get_password_hash, verify_password, create_access_token


class UserService:
    """Service for user-related operations."""
    
    @staticmethod
    def get_user_by_email(email: str) -> Optional[Dict[str, Any]]:
        """Get user by email address."""
        try:
            supabase = get_supabase()
            response = supabase.table("users_login").select("*").eq("email", email).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            print(f"Error getting user by email: {e}")
            return None
    
    @staticmethod
    def get_user_by_id(user_id: str) -> Optional[Dict[str, Any]]:
        """Get user by ID."""
        try:
            supabase = get_supabase()
            response = supabase.table("users_login").select("*").eq("id", user_id).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            print(f"Error getting user by id: {e}")
            return None
    
    @staticmethod
    def create_user(user_data: Dict[str, Any], ip_address: str = None) -> Optional[Dict[str, Any]]:
        """Create a new user."""
        try:
            supabase = get_supabase()
            
            # Check if user exists
            existing = supabase.table("users_login").select("id").eq("email", user_data["email"]).execute()
            if existing.data:
                return None
            
            # Hash password if provided
            if "password" in user_data:
                user_data["password"] = get_password_hash(user_data["password"])
            
            # Add metadata
            if ip_address:
                user_data["ip_address"] = ip_address
            
            # Insert user
            result = supabase.table("users_login").insert(user_data).execute()
            return result.data[0] if result.data else None
            
        except Exception as e:
            print(f"Error creating user: {e}")
            return None
    
    @staticmethod
    def update_user(user_id: str, update_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update user data."""
        try:
            supabase = get_supabase()
            result = supabase.table("users_login").update(update_data).eq("id", user_id).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            print(f"Error updating user: {e}")
            return None
    
    @staticmethod
    def update_last_login(user_id: str) -> bool:
        """Update user's last login timestamp."""
        try:
            supabase = get_supabase()
            supabase.table("users_login").update({
                "last_login": datetime.utcnow().isoformat()
            }).eq("id", user_id).execute()
            return True
        except Exception:
            return False
    
    @staticmethod
    def authenticate_user(email: str, password: str) -> Optional[Dict[str, Any]]:
        """Authenticate user with email and password."""
        user = UserService.get_user_by_email(email)
        
        if not user:
            return None
        
        if not user.get("password"):
            return None
        
        if not verify_password(password, user["password"]):
            return None
        
        # Update last login
        UserService.update_last_login(user["id"])
        
        return user
    
    @staticmethod
    def generate_auth_token(user: Dict[str, Any]) -> str:
        """Generate JWT token for user."""
        return create_access_token(data={"sub": user["email"]})
