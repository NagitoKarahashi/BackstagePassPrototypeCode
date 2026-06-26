from app.services.profiles_service import resolve_internal_user_id


def get_my_notifications_service(sb, external_auth_id: str, limit: int = 20):
    internal_user_id = resolve_internal_user_id(sb, external_auth_id)

    follows_resp = (
        sb.table("artist_follows")
        .select("artist_id")
        .eq("user_id", internal_user_id)
        .execute()
    )

    artist_ids = [row["artist_id"] for row in (follows_resp.data or []) if row.get("artist_id")]
    if not artist_ids:
        return {"items": []}

    events_resp = (
        sb.table("events")
        .select("id,title,artist,city,start_time,poster_url,created_at")
        .in_("artist", artist_ids)
        .order("start_time", desc=False)
        .limit(limit)
        .execute()
    )

    items = []
    for row in (events_resp.data or []):
        artist = row.get("artist")
        city = row.get("city")
        start_time = row.get("start_time")

        items.append(
            {
                "type": "new_show",
                "event_id": row["id"],
                "event_uuid": row["id"],
                "artist_id": None,
                "title": row.get("title"),
                "artist": artist,
                "city": city,
                "start_time": start_time,
                "poster_url": row.get("poster_url"),
                "created_at": row.get("created_at"),
                "read": False,
                "message": f"{artist or 'An artist you follow'} has a new event"
                           f"{f' in {city}' if city else ''}"
                           f"{f' starting at {start_time}' if start_time else ''}.",
            }
        )

    return {"items": items}