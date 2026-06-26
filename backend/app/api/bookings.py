from fastapi import APIRouter, HTTPException
from app.db.supabase_client import supabase
from app.schemas.bookings import (
    CreateBookingRequest,
    CreateBookingResponse,
    ConfirmBookingRequest,
    ConfirmBookingResponse,
)

router = APIRouter()

@router.post("/bookings", response_model=CreateBookingResponse)
def create_booking(req: CreateBookingRequest):
    try:
        result = supabase.rpc(
            "purchase_ticket",
            {
                "p_user_id": req.user_id,
                "p_event_id": req.event_id,
                "p_ticket_tier_id": req.ticket_tier_id,
                "p_quantity": req.quantity,
                "p_wallet_address": req.wallet_address,
                "p_device_id": req.device_id,
                "p_ip_address": req.ip_address,
            },
        ).execute()

        booking_id = result.data
        if not booking_id:
            raise HTTPException(status_code=400, detail="Failed to create booking")

        return CreateBookingResponse(
            booking_id=booking_id,
            status="pending",
            message="Booking created successfully",
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Create booking failed: {str(e)}")


@router.post("/bookings/{booking_id}/confirm", response_model=ConfirmBookingResponse)
def confirm_booking(booking_id: str, req: ConfirmBookingRequest):
    try:
        update_result = (
            supabase.table("orders")
            .update(
                {
                    "status": "paid",
                    "payment_ref": req.payment_ref,
                }
            )
            .eq("id", booking_id)
            .execute()
        )

        if not update_result.data:
            raise HTTPException(status_code=404, detail="Booking not found")

        issue_result = supabase.rpc(
            "issue_tickets_for_order",
            {"p_order_id": booking_id},
        ).execute()

        tickets_issued = issue_result.data or 0

        return ConfirmBookingResponse(
            booking_id=booking_id,
            booking_status="paid",
            tickets_issued=tickets_issued,
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Confirm booking failed: {str(e)}")