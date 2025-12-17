from supabase import create_client, Client
from app.config import settings

# Initialize Supabase Client
# We use the Service Role Key if available to have admin access (bypass RLS if needed for backend ops)
# Otherwise, use the Public Key. 
# CAUTION: Service Role Key gives full access.
key = settings.SUPABASE_SECRET_KEY if settings.SUPABASE_SECRET_KEY else settings.SUPABASE_KEY

supabase: Client = create_client(settings.SUPABASE_URL, key)

# Helper to get the client (useful for dependency injection if we needed it, 
# but supabase client is usually thread-safe and singleton-like)
def get_supabase() -> Client:
    return supabase
