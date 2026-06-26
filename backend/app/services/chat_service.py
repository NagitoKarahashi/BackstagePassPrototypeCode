from fastapi import HTTPException

from app.services.profiles_service import resolve_internal_user_id
from app.services.risk_service import evaluate_risk_context, should_block_chat

ALLOWED_CHAT_TICKET_STATUSES = ["active", "used"]


def _safe_display_name(profile: dict | None, fallback_user_id: str | None = None) -> str:
    profile = profile or {}
    return (
        profile.get("display_name")
        or profile.get("username")
        or profile.get("email")
        or (fallback_user_id or "Unknown user")
    )


def _ensure_event_chat_access(sb, internal_user_id: str, event_uuid: str):
    try:
        ticket_resp = (
            sb.table("tickets")
            .select("id, status")
            .eq("user_id", internal_user_id)
            .eq("event_uuid", event_uuid)
            .in_("status", ALLOWED_CHAT_TICKET_STATUSES)
            .limit(1)
            .execute()
        )
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail=f"Chat access check temporarily unavailable: {str(e)}",
        )

    ticket = ticket_resp.data[0] if ticket_resp.data else None
    if not ticket:
        raise HTTPException(
            status_code=403,
            detail="Only users with an active or used ticket can access this event chat room",
        )

    return ticket


def _ensure_chat_risk_allowed(sb, internal_user_id: str, event_uuid: str):
    risk_ctx = evaluate_risk_context(
        sb,
        {
            "user_id": internal_user_id,
            "event_uuid": event_uuid,
        },
        lang="en",
    )

    if should_block_chat(risk_ctx):
        raise HTTPException(
            status_code=403,
            detail={
                "message": "Chat access is temporarily restricted due to risk signals.",
                "risk_level": risk_ctx["risk_level"],
                "risk_type": risk_ctx["risk_type"],
                "recommended_action": risk_ctx["recommended_action"],
                "reasons": risk_ctx["reasons"],
            },
        )

    return risk_ctx


def get_event_chat_room_service(sb, external_auth_id: str, event_uuid: str):
    internal_user_id = resolve_internal_user_id(sb, external_auth_id)

    _ensure_event_chat_access(sb, internal_user_id, event_uuid)
    _ensure_chat_risk_allowed(sb, internal_user_id, event_uuid)

    try:
        room_resp = (
            sb.table("chat_rooms")
            .select("*")
            .eq("event_id", event_uuid)
            .eq("room_type", "event")
            .limit(1)
            .execute()
        )
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail=f"Chat room lookup temporarily unavailable: {str(e)}",
        )

    room = room_resp.data[0] if room_resp.data else None
    if not room:
        raise HTTPException(status_code=404, detail="Chat room not found")

    return room


def get_event_messages_service(sb, external_auth_id: str, event_uuid: str):
    room = get_event_chat_room_service(sb, external_auth_id, event_uuid)

    try:
        msg_resp = (
            sb.table("chat_messages")
            .select("*")
            .eq("room_id", room["id"])
            .order("created_at", desc=False)
            .execute()
        )
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail=f"Chat messages temporarily unavailable: {str(e)}",
        )

    messages = msg_resp.data or []
    if not messages:
        return {"room": room, "items": []}

    user_ids = list({m["sender_user_id"] for m in messages if m.get("sender_user_id")})
    profile_map = {}

    if user_ids:
        try:
            profiles_resp = (
                sb.table("profiles")
                .select("id, username, display_name, email")
                .in_("id", user_ids)
                .execute()
            )
            for p in profiles_resp.data or []:
                profile_map[p["id"]] = p
        except Exception:
            profile_map = {}

    items = []
    for m in messages:
        sender_user_id = m.get("sender_user_id")
        message_text = m.get("message_text")
        profile = profile_map.get(sender_user_id, {})
        sender_name = _safe_display_name(profile, sender_user_id)

        items.append(
            {
                "id": m.get("id"),
                "room_id": m.get("room_id"),
                "user_id": sender_user_id,
                "sender_user_id": sender_user_id,
                "content": message_text,
                "message": message_text,
                "text": message_text,
                "message_text": message_text,
                "created_at": m.get("created_at"),
                "edited_at": m.get("edited_at"),
                "is_pinned": m.get("is_pinned"),
                "username": profile.get("username"),
                "display_name": profile.get("display_name"),
                "email": profile.get("email"),
                "sender_name": sender_name,
                "user_name": sender_name,
            }
        )

    return {"room": room, "items": items}


def post_event_message_service(sb, external_auth_id: str, event_uuid: str, content: str):
    if not content or not content.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty")

    internal_user_id = resolve_internal_user_id(sb, external_auth_id)

    room = get_event_chat_room_service(sb, external_auth_id, event_uuid)
    risk_ctx = _ensure_chat_risk_allowed(sb, internal_user_id, event_uuid)

    try:
        insert_resp = (
            sb.table("chat_messages")
            .insert(
                {
                    "room_id": room["id"],
                    "sender_user_id": internal_user_id,
                    "message_text": content.strip(),
                }
            )
            .execute()
        )
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail=f"Failed to send message temporarily: {str(e)}",
        )

    created = insert_resp.data[0] if insert_resp.data else None
    if not created:
        raise HTTPException(status_code=400, detail="Failed to create message")

    try:
        profile_resp = (
            sb.table("profiles")
            .select("id, username, display_name, email")
            .eq("id", internal_user_id)
            .limit(1)
            .execute()
        )
        profile = profile_resp.data[0] if profile_resp.data else {}
    except Exception:
        profile = {}

    sender_name = _safe_display_name(profile, created.get("sender_user_id"))
    message_text = created.get("message_text")

    return {
        "id": created.get("id"),
        "room_id": created.get("room_id"),
        "user_id": created.get("sender_user_id"),
        "sender_user_id": created.get("sender_user_id"),
        "content": message_text,
        "message": message_text,
        "text": message_text,
        "message_text": message_text,
        "created_at": created.get("created_at"),
        "edited_at": created.get("edited_at"),
        "is_pinned": created.get("is_pinned"),
        "username": profile.get("username"),
        "display_name": profile.get("display_name"),
        "email": profile.get("email"),
        "sender_name": sender_name,
        "user_name": sender_name,
        "risk": {
            "risk_score": risk_ctx["risk_score"],
            "risk_level": risk_ctx["risk_level"],
            "risk_type": risk_ctx["risk_type"],
        },
    }


def list_my_chat_rooms_service(sb, external_auth_id: str):
    internal_user_id = resolve_internal_user_id(sb, external_auth_id)

    tickets_resp = (
        sb.table("tickets")
        .select("event_uuid, status")
        .eq("user_id", internal_user_id)
        .in_("status", ALLOWED_CHAT_TICKET_STATUSES)
        .execute()
    )

    tickets = tickets_resp.data or []
    if not tickets:
        return []

    event_uuid_to_status = {}
    for t in tickets:
        event_uuid = t.get("event_uuid")
        status = t.get("status")
        if event_uuid and event_uuid not in event_uuid_to_status:
            event_uuid_to_status[event_uuid] = status

    event_ids = list(event_uuid_to_status.keys())

    rooms_resp = (
        sb.table("chat_rooms")
        .select("*")
        .eq("room_type", "event")
        .in_("event_id", event_ids)
        .execute()
    )
    rooms = rooms_resp.data or []

    try:
        events_resp = (
            sb.table("events")
            .select("id, title, artist, city, genre, start_time, poster_url, description")
            .in_("id", event_ids)
            .execute()
        )
        events = events_resp.data or []
    except Exception:
        events = []

    event_map = {e["id"]: e for e in events}

    items = []
    for room in rooms:
        event_uuid = room.get("event_id")
        event = event_map.get(event_uuid, {})

        items.append(
            {
                "room_id": room.get("id"),
                "room_name": room.get("room_name"),
                "room_type": room.get("room_type"),
                "event_uuid": event_uuid,
                "title": event.get("title"),
                "artist": event.get("artist"),
                "city": event.get("city"),
                "genre": event.get("genre"),
                "start_time": event.get("start_time"),
                "poster_url": event.get("poster_url"),
                "description": event.get("description"),
                "ticket_status": event_uuid_to_status.get(event_uuid),
            }
        )

    return items