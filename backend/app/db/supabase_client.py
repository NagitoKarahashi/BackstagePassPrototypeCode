from supabase import Client, create_client
from app.core.config import get_settings

settings = get_settings()

supabase: Client = create_client(
    settings.supabase_url,
    settings.supabase_service_role_key,
)

def get_supabase_client() -> Client:
    return supabase