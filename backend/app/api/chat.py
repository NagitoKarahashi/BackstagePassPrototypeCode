from fastapi import APIRouter, Query
from pydantic import BaseModel

from app.schemas.chat import (
    ChatRoomResponse,
    ChatMessageCreateRequest,
    ChatMessageResponse,
)
from app.services.chat_service import (
    get_room_by_event,
    get_messages,
    send_message,
)

router = APIRouter(prefix="/chat", tags=["chat"])


class EventChatMessageCreateRequest(BaseModel):
    sender_user_id: str
    message_text: str


@router.get("/room/by-event/{event_id}", response_model=ChatRoomResponse)
def get_chat_room_by_event(event_id: str):
    return get_room_by_event(event_id)


@router.get("/room/{room_id}/messages", response_model=list[ChatMessageResponse])
def list_chat_messages(room_id: str, limit: int = Query(default=50, ge=1, le=200)):
    return get_messages(room_id, limit)


@router.post("/messages", response_model=ChatMessageResponse)
def create_chat_message(req: ChatMessageCreateRequest):
    return send_message(
        room_id=req.room_id,
        sender_user_id=req.sender_user_id,
        message_text=req.message_text,
    )


# 新增：直接按 event_id 取消息
@router.get("/events/{event_id}/messages", response_model=list[ChatMessageResponse])
def list_event_chat_messages(event_id: str, limit: int = Query(default=50, ge=1, le=200)):
    room = get_room_by_event(event_id)
    return get_messages(room["room_id"], limit)


# 新增：直接按 event_id 发消息
@router.post("/events/{event_id}/messages", response_model=ChatMessageResponse)
def create_event_chat_message(event_id: str, req: EventChatMessageCreateRequest):
    room = get_room_by_event(event_id)
    return send_message(
        room_id=room["room_id"],
        sender_user_id=req.sender_user_id,
        message_text=req.message_text,
    )