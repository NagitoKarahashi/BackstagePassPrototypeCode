from fastapi import APIRouter, Query, HTTPException
from typing import Optional
from app.services.events_service import (
    list_events,
    get_event_by_id,
    get_hot_near_you,
)

router = APIRouter()

@router.get("/events")
def get_events(
    city: Optional[str] = None,
    genre: Optional[str] = None,
    artist: Optional[str] = None,
    search: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=50),
):
    return list_events(
        city=city,
        genre=genre,
        artist=artist,
        search=search,
        page=page,
        page_size=page_size,
    )

@router.get("/events/hot-near-you")
def hot_near_you(city: Optional[str] = None):
    return get_hot_near_you(city=city)

@router.get("/events/{event_id}")
def get_event_detail(event_id: str):
    event = get_event_by_id(event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    return event