from typing import List, Optional
from pydantic import BaseModel


class NotificationItemOut(BaseModel):
    type: str
    event_id: str
    artist_id: Optional[str] = None
    title: Optional[str] = None
    artist: Optional[str] = None
    city: Optional[str] = None
    start_time: Optional[str] = None
    poster_url: Optional[str] = None