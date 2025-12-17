"""
Supabase Client
Database connection wrapper for Supabase.
"""
from supabase import create_client, Client
from app.core.config import settings


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
