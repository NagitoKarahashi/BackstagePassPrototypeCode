from app.services.profiles_service import resolve_internal_user_id


def follow_artist_service(sb, external_auth_id: str, artist_id: str):
    internal_user_id = resolve_internal_user_id(sb, external_auth_id)

    resp = (
        sb.table("artist_follows")
        .upsert(
            {
                "user_id": internal_user_id,
                "artist_id": artist_id,
            },
            on_conflict="user_id,artist_id",
        )
        .execute()
    )
    return {"ok": True, "item": resp.data[0] if resp.data else None}


def unfollow_artist_service(sb, external_auth_id: str, artist_id: str):
    internal_user_id = resolve_internal_user_id(sb, external_auth_id)

    (
        sb.table("artist_follows")
        .delete()
        .eq("user_id", internal_user_id)
        .eq("artist_id", artist_id)
        .execute()
    )
    return {"ok": True}


def list_followed_artists_service(sb, external_auth_id: str):
    internal_user_id = resolve_internal_user_id(sb, external_auth_id)

    resp = (
        sb.table("artist_follows")
        .select("*")
        .eq("user_id", internal_user_id)
        .order("created_at", desc=True)
        .execute()
    )
    return {"items": resp.data or []}