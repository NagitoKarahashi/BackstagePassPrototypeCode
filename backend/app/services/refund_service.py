from fastapi import HTTPException
from app.services.risk_service import (
    evaluate_risk_context,
    should_block_refund,
    should_hold_refund_for_review,
    build_risk_restriction_message,
)


def _get_ticket_or_404(sb, ticket_id: str):
    ticket_resp = (
        sb.table("tickets")
        .select("id, user_id, status, is_listed, transfer_locked, resale_allowed, qr_payload")
        .eq("id", ticket_id)
        .limit(1)
        .execute()
    )
    if not ticket_resp.data:
        raise HTTPException(status_code=404, detail="Ticket not found")
    return ticket_resp.data[0]


def _cancel_active_listing_if_any(sb, ticket_id: str):
    try:
        active_listing_resp = (
            sb.table("marketplace_listings")
            .select("id, status")
            .eq("ticket_id", ticket_id)
            .eq("status", "active")
            .order("created_at", desc=True)
            .limit(1)
            .execute()
        )

        if active_listing_resp.data:
            listing_id = active_listing_resp.data[0]["id"]
            sb.table("marketplace_listings").update(
                {
                    "status": "cancelled",
                }
            ).eq("id", listing_id).execute()
    except Exception:
        pass


def request_refund_service(
    sb,
    ticket_id: str,
    user_id: str,
    device_id: str | None = None,
    ip_address: str | None = None,
    risk_overrides: dict | None = None,
    simulate_only: bool = False,
):
    ticket = _get_ticket_or_404(sb, ticket_id)

    if str(ticket["user_id"]) != str(user_id):
        raise HTTPException(status_code=403, detail="You do not own this ticket")

    if ticket["status"] in {"used", "expired", "refunded"}:
        raise HTTPException(
            status_code=400,
            detail=f"Ticket in status '{ticket['status']}' cannot be refunded",
        )

    if ticket.get("is_listed"):
        raise HTTPException(
            status_code=400,
            detail="Listed ticket must be delisted before refund",
        )

    if ticket.get("transfer_locked"):
        raise HTTPException(
            status_code=400,
            detail="Transfer-locked ticket cannot be refunded",
        )

    payload = {
        "ticket_id": ticket_id,
        "user_id": user_id,
        "device_id": device_id,
        "ip_address": ip_address,
    }
    if risk_overrides:
        payload.update(risk_overrides)

    risk_ctx = evaluate_risk_context(
        sb,
        payload,
        lang="en",
    )

    if should_block_refund(risk_ctx):
        raise HTTPException(
            status_code=403,
            detail={
                "message": build_risk_restriction_message("refund", lang="en"),
                "risk_level": risk_ctx["risk_level"],
                "risk_type": risk_ctx["risk_type"],
                "reasons": risk_ctx["reasons"],
                "recommended_action": risk_ctx["recommended_action"],
            },
        )

    if should_hold_refund_for_review(risk_ctx):
        return {
            "status": "review_required",
            "message": "Refund request has been received and requires additional review.",
            "risk": {
                "risk_score": risk_ctx["risk_score"],
                "risk_level": risk_ctx["risk_level"],
                "risk_type": risk_ctx["risk_type"],
                "reasons": risk_ctx["reasons"],
                "recommended_action": risk_ctx["recommended_action"],
            },
        }

    if simulate_only:
        return {
            "status": "requested",
            "message": "Refund simulation passed.",
            "risk": {
                "risk_score": risk_ctx["risk_score"],
                "risk_level": risk_ctx["risk_level"],
                "risk_type": risk_ctx["risk_type"],
                "reasons": risk_ctx["reasons"],
                "recommended_action": risk_ctx["recommended_action"],
            },
        }

    try:
        refund_resp = sb.rpc(
            "refund_ticket_atomic",
            {
                "p_ticket_id": ticket_id,
                "p_user_id": user_id,
            }
        ).execute()
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Refund RPC failed: {str(e)}")

    if not refund_resp.data:
        raise HTTPException(status_code=400, detail="Failed to request refund")

    # Refund succeeded: enforce post-refund consistency
    _cancel_active_listing_if_any(sb, ticket_id)

    try:
        sb.table("tickets").update(
            {
                "status": "refunded",
                "is_listed": False,
                "transfer_locked": True,
                "resale_allowed": False,
                "qr_payload": None,
            }
        ).eq("id", ticket_id).execute()
    except Exception:
        pass

    return {
        "status": "requested",
        "result": refund_resp.data,
        "risk": {
            "risk_score": risk_ctx["risk_score"],
            "risk_level": risk_ctx["risk_level"],
            "risk_type": risk_ctx["risk_type"],
            "reasons": risk_ctx["reasons"],
            "recommended_action": risk_ctx["recommended_action"],
        },
    }