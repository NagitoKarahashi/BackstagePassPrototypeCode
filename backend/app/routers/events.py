from fastapi import APIRouter, Depends, Query
from supabase import Client

from app.core.deps import supabase_dep
from app.services.events_service import (
    list_events_service,
    get_hot_near_you_service,
    get_recommended_events_service,
    get_event_by_code_service,
    get_event_by_id_service,
)

router = APIRouter(prefix="/events", tags=["events"])


@router.get("")
def list_events(
    q: str | None = None,
    city: str | None = None,
    genre: str | None = None,
    artist: str | None = None,
    country: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    tags: list[str] = Query(default=[]),
    status: str | None = "published",
    only_available: bool = False,
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    sb: Client = Depends(supabase_dep),
):
    return list_events_service(
        sb=sb,
        q=q,
        city=city,
        genre=genre,
        artist=artist,
        country=country,
        date_from=date_from,
        date_to=date_to,
        tags=tags,
        status=status,
        only_available=only_available,
        limit=limit,
        offset=offset,
    )


@router.get("/hot-near-you")
def hot_near_you(
    city: str | None = None,
    limit: int = Query(default=10, ge=1, le=50),
    sb: Client = Depends(supabase_dep),
):
    return get_hot_near_you_service(
        sb=sb,
        city=city,
        limit=limit,
    )


@router.get("/recommended")
def recommended(
    user_id: str,
    limit: int = Query(default=10, ge=1, le=50),
    sb: Client = Depends(supabase_dep),
):
    return get_recommended_events_service(
        sb=sb,
        user_id=user_id,
        limit=limit,
    )


@router.get("/code/{event_code}")
def get_event_by_code(
    event_code: str,
    sb: Client = Depends(supabase_dep),
):
    return get_event_by_code_service(
        sb=sb,
        event_code=event_code,
    )


@router.get("/{event_id}")
def get_event_by_id(
    event_id: str,
    sb: Client = Depends(supabase_dep),
):
    return get_event_by_id_service(
        sb=sb,
        event_id=event_id,
    )