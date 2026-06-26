from typing import Any, Dict

from fastapi import HTTPException
from supabase import Client

from app.schemas.support_enquiry import SupportEnquiryCreate
from app.services.profiles_service import resolve_internal_user_id


def create_support_enquiry_service(
    sb: Client,
    external_auth_id: str,
    payload: SupportEnquiryCreate,
) -> Dict[str, Any]:
    internal_user_id = resolve_internal_user_id(sb, external_auth_id)

    insert_data = {
        "user_id": internal_user_id,
        "category": payload.category,
        "subject": payload.subject.strip(),
        "message": payload.message.strip(),
        "order_id": str(payload.order_id) if payload.order_id else None,
        "event_uuid": str(payload.event_uuid) if payload.event_uuid else None,
        "ticket_id": str(payload.ticket_id) if payload.ticket_id else None,
        "status": "open",
        "source": payload.source,
    }

    try:
        resp = sb.table("support_enquiries").insert(insert_data).execute()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create support enquiry: {e}")

    rows = getattr(resp, "data", None) or []
    if not rows:
        raise HTTPException(status_code=500, detail="Support enquiry creation returned no data")

    return rows[0]


def list_my_support_enquiries_service(
    sb: Client,
    external_auth_id: str,
    limit: int = 50,
    offset: int = 0,
) -> Dict[str, Any]:
    internal_user_id = resolve_internal_user_id(sb, external_auth_id)

    try:
        resp = (
            sb.table("support_enquiries")
            .select("*", count="exact")
            .eq("user_id", internal_user_id)
            .order("created_at", desc=True)
            .range(offset, offset + limit - 1)
            .execute()
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list support enquiries: {e}")

    items = getattr(resp, "data", None) or []
    total = getattr(resp, "count", None)
    if total is None:
        total = len(items)

    return {"items": items, "total": total}