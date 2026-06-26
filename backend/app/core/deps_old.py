from fastapi import HTTPException
from supabase import Client
from .supabase_client import get_supabase


def supabase_dep() -> Client:
    try:
        return get_supabase()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Supabase not configured: {exc}")
