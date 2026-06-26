from datetime import datetime
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException
from supabase import Client

from app.core.deps import supabase_dep, current_user_dep
from app.schemas.bookings import BookingCreateRequest, BookingConfirmRequest, BookingCancelRequest
from app.services.profiles_service import resolve_internal_user_id

router = APIRouter(prefix="/bookings", tags=["bookings"])


def _get_event_or_404(sb: Client, event_id: str):
    event = (
        sb.table("events")
        .select("id,title,ticket_inventory,tickets_remaining,status")
        .eq("id", event_id)
        .limit(1)
        .execute()
    )
    if not event.data:
        raise HTTPException(status_code=404, detail="Event not found")
    return event.data[0]


@router.post("")
def create_booking(
    payload: BookingCreateRequest,
    current_user=Depends(current_user_dep),
    sb: Client = Depends(supabase_dep),
):
    internal_user_id = resolve_internal_user_id(sb, current_user.id)

    event = _get_event_or_404(sb, payload.event_id)
    remaining = int(event.get("tickets_remaining") or 0)
    if remaining < payload.quantity:
        raise HTTPException(status_code=409, detail="Not enough tickets remaining")

    unit_price = payload.unit_price or 0
    booking = {
        "id": str(uuid4()),
        "user_id": internal_user_id,
        "event_id": payload.event_id,
        "quantity": payload.quantity,
        "status": "pending",
        "currency": payload.currency,
        "unit_price": unit_price,
        "total_amount": round(unit_price * payload.quantity, 2),
        "payment_method": payload.payment_method,
        "payment_ref": payload.payment_ref,
        "wallet_address": payload.wallet_address,
        "device_id": payload.device_id,
        "ip_address": payload.ip_address,
        "created_at": datetime.utcnow().isoformat(),
    }
    created = sb.table("orders").insert(booking).execute()
    return created.data[0]


@router.post("/{booking_id}/confirm")
def confirm_booking(booking_id: str, payload: BookingConfirmRequest, sb: Client = Depends(supabase_dep)):
    order_resp = sb.table("orders").select("*").eq("id", booking_id).limit(1).execute()
    if not order_resp.data:
        raise HTTPException(status_code=404, detail="Booking not found")
    order = order_resp.data[0]
    if order.get("status") == "confirmed":
        return order
    if order.get("status") == "cancelled":
        raise HTTPException(status_code=409, detail="Cancelled booking cannot be confirmed")

    event = _get_event_or_404(sb, order["event_id"])
    remaining = int(event.get("tickets_remaining") or 0)
    qty = int(order["quantity"])
    if remaining < qty:
        raise HTTPException(status_code=409, detail="Not enough tickets remaining at confirm time")

    updated_order = sb.table("orders").update({
        "status": "confirmed",
        "payment_ref": payload.payment_ref or order.get("payment_ref"),
        "paid_amount": payload.paid_amount,
        "confirmed_at": datetime.utcnow().isoformat(),
    }).eq("id", booking_id).execute()

    sb.table("events").update({"tickets_remaining": remaining - qty}).eq("id", order["event_id"]).execute()

    tickets = []
    for idx in range(qty):
        t = {
            "id": str(uuid4()),
            "order_id": booking_id,
            "event_id": order["event_id"],
            "owner_user_id": order["user_id"],
            "ticket_code": f"TKT-{booking_id[:8]}-{idx+1}",
            "status": "active",
            "qr_code": f"qr://ticket/{booking_id}:{idx+1}",
            "created_at": datetime.utcnow().isoformat(),
        }
        tickets.append(t)
    if tickets:
        sb.table("tickets").insert(tickets).execute()

    return {
        "booking": updated_order.data[0] if updated_order.data else None,
        "tickets_created": len(tickets),
    }


@router.post("/{booking_id}/cancel")
def cancel_booking(booking_id: str, payload: BookingCancelRequest, sb: Client = Depends(supabase_dep)):
    order_resp = sb.table("orders").select("*").eq("id", booking_id).limit(1).execute()
    if not order_resp.data:
        raise HTTPException(status_code=404, detail="Booking not found")
    order = order_resp.data[0]
    if order.get("status") == "cancelled":
        return order

    was_confirmed = order.get("status") == "confirmed"
    updated = sb.table("orders").update({
        "status": "cancelled",
        "cancel_reason": payload.reason,
        "cancelled_at": datetime.utcnow().isoformat(),
    }).eq("id", booking_id).execute()

    if was_confirmed:
        event = _get_event_or_404(sb, order["event_id"])
        restored = int(event.get("tickets_remaining") or 0) + int(order["quantity"])
        sb.table("events").update({"tickets_remaining": restored}).eq("id", order["event_id"]).execute()
        sb.table("tickets").update({"status": "cancelled"}).eq("order_id", booking_id).execute()

    return updated.data[0] if updated.data else {"message": "Booking cancelled"}