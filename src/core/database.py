"""
Database Client Setup
Supabase client initialization and access.
"""
from supabase import create_client, Client
from src.core.config import settings


# Initialize Supabase Client
# Use Service Role Key for admin access (bypass RLS) or Public Key
key = settings.SUPABASE_SECRET_KEY if settings.SUPABASE_SECRET_KEY else settings.SUPABASE_KEY

supabase: Client = create_client(settings.SUPABASE_URL, key)


def get_supabase() -> Client:
    """
    Get Supabase client instance.
    
    This can be used as a FastAPI dependency or called directly.
    The client is thread-safe and singleton-like.
    
    Returns:
        Client: Supabase client instance
    """
    return supabase


# Initialize Admin Client (Service Role) specifically
# This is useful if we want to be explicit about using the Service Role Key
admin_key = settings.SUPABASE_SECRET_KEY
supabase_admin: Client = create_client(settings.SUPABASE_URL, admin_key) if admin_key else supabase

def get_supabase_admin() -> Client:
    """
    Get Supabase admin client (Service Role).
    Use this for backend operations that need to bypass RLS.
    """
    return supabase_admin
