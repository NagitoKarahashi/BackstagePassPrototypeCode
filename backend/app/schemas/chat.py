from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class ChatRoomOut(BaseModel):
    id: str
    event_id: str
    room_name: str
    room_type: str = "event"
    created_at: Optional[datetime] = None


class ChatMessageCreateRequest(BaseModel):
    content: str = Field(min_length=1, max_length=2000)


class ChatMessageOut(BaseModel):
    id: str
    room_id: str
    sender_user_id: str
    message_text: str
    created_at: Optional[datetime] = None
    edited_at: Optional[datetime] = None
    is_pinned: bool = False