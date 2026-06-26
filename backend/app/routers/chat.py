from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from supabase import Client

from app.core.deps import supabase_dep, get_current_user
from app.services.chat_service import (
    list_my_chat_rooms_service,
    get_event_chat_room_service,
    get_event_messages_service,
    post_event_message_service,
)

router = APIRouter(prefix="/chat", tags=["chat"])


class CreateChatMessageRequest(BaseModel):
    content: str = Field(min_length=1, max_length=2000)


@router.get("/my-rooms")
def list_my_chat_rooms(
    sb: Client = Depends(supabase_dep),
    current_user=Depends(get_current_user),
):
    return list_my_chat_rooms_service(sb, str(current_user.id))


@router.get("/events/{event_uuid}/room")
def get_event_chat_room(event_uuid: str, sb: Client = Depends(supabase_dep), current_user=Depends(get_current_user)):
    return get_event_chat_room_service(sb, str(current_user.id), event_uuid)


@router.get("/events/{event_uuid}/messages")
def get_event_messages(event_uuid: str, sb: Client = Depends(supabase_dep), current_user=Depends(get_current_user)):
    return get_event_messages_service(sb, str(current_user.id), event_uuid)


@router.post("/events/{event_uuid}/messages")
def post_event_message(
    event_uuid: str,
    req: CreateChatMessageRequest,
    sb: Client = Depends(supabase_dep),
    current_user=Depends(get_current_user),
):
    return post_event_message_service(sb, str(current_user.id), event_uuid, req.content)