from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class EventOut(BaseModel):
    id: str
    event_code: str
    title: str
    artist: Optional[str] = None
    genre: Optional[str] = None
    city: Optional[str] = None
    country: Optional[str] = None
    venue_name: Optional[str] = None
    tags: list[str] = Field(default_factory=list)
    start_time: Optional[datetime] = None
    starts_at: Optional[datetime] = None
    ends_at: Optional[datetime] = None
    description: Optional[str] = None
    price: Optional[float] = None
    stock_total: Optional[int] = None
    stock_left: Optional[int] = None
    poster_url: Optional[str] = None
    cover_url: Optional[str] = None
    status: Optional[str] = None
    created_at: Optional[datetime] = None


class EventListResponse(BaseModel):
    items: list[EventOut]
    total: int
    limit: int
    offset: int


class EventQueryParams(BaseModel):
    q: Optional[str] = None
    artist: Optional[str] = None
    genre: Optional[str] = None
    city: Optional[str] = None
    country: Optional[str] = None
    date_from: Optional[str] = None
    date_to: Optional[str] = None
    tags: list[str] = Field(default_factory=list)
    status: Optional[str] = "published"
    only_available: bool = False
    limit: int = 20
    offset: int = 0