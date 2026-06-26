from app.db.supabase_client import supabase

def get_my_profile(external_auth_id: str):
    result = (
        supabase.table("profiles")
        .select("*")
        .eq("external_auth_id", external_auth_id)
        .limit(1)
        .execute()
    )
    if result.data:
        return result.data[0]
    return {"external_auth_id": external_auth_id, "profile_exists": False}


def update_my_profile(external_auth_id: str, payload: dict):
    existing = (
        supabase.table("profiles")
        .select("id")
        .eq("external_auth_id", external_auth_id)
        .limit(1)
        .execute()
    )

    if not existing.data:
        return {"updated": False, "data": None, "detail": "Profile not found"}

    profile_id = existing.data[0]["id"]
    result = (
        supabase.table("profiles")
        .update(payload)
        .eq("id", profile_id)
        .execute()
    )
    return {"updated": True, "data": result.data}