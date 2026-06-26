from fastapi import HTTPException
from pathlib import Path
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"


EVENT_SELECT = (
    "id, event_code, title, artist, genre, city, country, "
    "venue_name, tags, description, price, stock_total, stock_left, "
    "poster_url, cover_url, start_time, starts_at, ends_at, status, created_at"
)


def list_events_service(
    sb,
    q=None,
    city=None,
    genre=None,
    artist=None,
    country=None,
    date_from=None,
    date_to=None,
    tags=None,
    status="published",
    only_available=False,
    limit=20,
    offset=0,
):
    query = sb.table("events").select(EVENT_SELECT, count="exact")

    if status:
        query = query.eq("status", status)

    if city:
        query = query.eq("city", city)

    if country:
        query = query.eq("country", country)

    if genre:
        query = query.eq("genre", genre)

    if artist:
        query = query.ilike("artist", f"%{artist}%")

    if date_from:
        query = query.gte("starts_at", date_from)

    if date_to:
        query = query.lte("starts_at", date_to)

    if only_available:
        query = query.gt("stock_left", 0)

    result = (
        query
        .order("starts_at", desc=False)
        .range(offset, offset + limit - 1)
        .execute()
    )

    items = result.data or []

    if q:
        q_lower = q.strip().lower()
        items = [
            item for item in items
            if q_lower in (item.get("title") or "").lower()
            or q_lower in (item.get("artist") or "").lower()
            or q_lower in (item.get("genre") or "").lower()
            or q_lower in (item.get("city") or "").lower()
            or q_lower in (item.get("country") or "").lower()
            or q_lower in (item.get("venue_name") or "").lower()
            or q_lower in (item.get("description") or "").lower()
        ]

    if tags:
        normalized_tags = {t.lower() for t in tags}
        filtered = []
        for item in items:
            item_tags = item.get("tags") or []
            item_tags_lower = {str(t).lower() for t in item_tags}
            if normalized_tags.issubset(item_tags_lower):
                filtered.append(item)
        items = filtered

    return {
        "items": items,
        "total": result.count or 0,
        "limit": limit,
        "offset": offset,
    }


def get_event_by_id_service(sb, event_id: str):
    res = (
        sb.table("events")
        .select(EVENT_SELECT)
        .eq("id", event_id)
        .limit(1)
        .execute()
    )
    if not res.data:
        raise HTTPException(status_code=404, detail="Event not found")
    return res.data[0]


def get_event_by_code_service(sb, event_code: str):
    res = (
        sb.table("events")
        .select(EVENT_SELECT)
        .eq("event_code", event_code)
        .limit(1)
        .execute()
    )
    if not res.data:
        raise HTTPException(status_code=404, detail="Event not found")
    return res.data[0]


def get_hot_near_you_service(sb, city=None, limit=10):
    query = (
        sb.table("events")
        .select(EVENT_SELECT)
        .eq("status", "published")
        .gt("stock_left", 0)
    )

    if city:
        query = query.eq("city", city)

    res = query.order("starts_at", desc=False).limit(limit).execute()
    return {"items": res.data or []}


def get_recommended_events_service(sb, user_id, limit=10):
    profile = (
        sb.table("profiles")
        .select("city, preferred_genres")
        .eq("id", user_id)
        .limit(1)
        .execute()
    )

    city = None
    genre = None

    if profile.data:
        city = profile.data[0].get("city")
        prefs = profile.data[0].get("preferred_genres") or []
        if prefs:
            genre = prefs[0]

    query = (
        sb.table("events")
        .select(EVENT_SELECT)
        .eq("status", "published")
        .gt("stock_left", 0)
    )

    if city:
        query = query.eq("city", city)

    if genre:
        query = query.eq("genre", genre)

    res = query.order("starts_at", desc=False).limit(limit).execute()
    return {"items": res.data or []}


def get_events_df() -> pd.DataFrame:
    events_path = DATA_DIR / "events.csv"

    if not events_path.exists():
        return pd.DataFrame(
            columns=["event_id", "title", "artist", "genre", "city", "start_time", "desc"]
        )

    df = pd.read_csv(events_path)

    expected_cols = ["event_id", "title", "artist", "genre", "city", "start_time", "desc"]
    for col in expected_cols:
        if col not in df.columns:
            df[col] = None

    return df