from supabase import Client, create_client
from .config import get_settings


_client: Client | None = None


def get_supabase() -> Client:
    global _client
    if _client is None:
        settings = get_settings()
        if not settings.supabase_url or not settings.supabase_service_role_key:
            raise RuntimeError("Missing SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY in environment")
        _client = create_client(settings.supabase_url, settings.supabase_service_role_key)
    return _client
