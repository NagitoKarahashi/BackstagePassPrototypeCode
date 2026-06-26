from fastapi import HTTPException

from app.services.profiles_service import resolve_internal_user_id
from app.services.risk_service import (
    evaluate_risk_context,
    should_block_transfer_like_action,
    build_risk_restriction_message,
)


def request_transfer_service(
    sb,
    ticket_id: str,
    from_user_id: str,
    to_user_id: str,
    to_wallet_address: str | None = None,
    note: str | None = None,
    device_id: str | None = None,
    ip_address: str | None = None,
):
    from_internal_user_id = resolve_internal_user_id(sb, from_user_id)

    ticket_res = (
        sb.table("tickets")
        .select("id, user_id, status, is_listed, transfer_locked, resale_allowed, event_uuid")
        .eq("id", ticket_id)
        .limit(1)
        .execute()
    )

    if not ticket_res.data:
        raise HTTPException(status_code=404, detail="Ticket not found")

    ticket = ticket_res.data[0]

    if ticket["user_id"] != from_internal_user_id:
        raise HTTPException(status_code=403, detail="You are not the current owner of this ticket")

    if ticket["status"] in {"used", "expired", "refunded"}:
        raise HTTPException(status_code=400, detail=f"Ticket in status '{ticket['status']}' cannot be transferred")

    if ticket.get("is_listed"):
        raise HTTPException(status_code=400, detail="Listed ticket cannot be transferred directly")

    if ticket.get("transfer_locked"):
        raise HTTPException(status_code=403, detail="Ticket transfer is currently locked")

    transfer_attempts_recent = 0
    try:
        transfer_attempts_recent_resp = (
            sb.table("ticket_transfer_history")
            .select("id", count="exact")
            .eq("from_user_id", from_internal_user_id)
            .execute()
        )
        transfer_attempts_recent = int(transfer_attempts_recent_resp.count or 0)
    except Exception:
        transfer_attempts_recent = 0

    risk_ctx = evaluate_risk_context(
        sb,
        {
            "user_id": from_internal_user_id,
            "event_uuid": ticket.get("event_uuid"),
            "device_id": device_id,
            "ip_address": ip_address,
            "transfer_attempts_recent": transfer_attempts_recent + 1,
        },
        lang="en",
    )

    if should_block_transfer_like_action(risk_ctx):
        raise HTTPException(
            status_code=403,
            detail={
                "message": build_risk_restriction_message("transfer", lang="en"),
                "risk_level": risk_ctx["risk_level"],
                "risk_type": risk_ctx["risk_type"],
                "reasons": risk_ctx["reasons"],
                "recommended_action": risk_ctx["recommended_action"],
            },
        )

    target_profile = (
        sb.table("profiles")
        .select("id, wallet_address")
        .eq("id", to_user_id)
        .limit(1)
        .execute()
    )
    if not target_profile.data:
        raise HTTPException(status_code=404, detail="Target user profile not found")

    from_profile = (
        sb.table("profiles")
        .select("id, wallet_address")
        .eq("id", from_internal_user_id)
        .limit(1)
        .execute()
    )

    from_wallet_address = from_profile.data[0].get("wallet_address") if from_profile.data else None

    if to_wallet_address:
        try:
            sb.table("profiles").update({"wallet_address": to_wallet_address}).eq("id", to_user_id).execute()
        except Exception:
            pass
    else:
        to_wallet_address = target_profile.data[0].get("wallet_address")

    try:
        sb.table("tickets").update(
            {
                "user_id": to_user_id,
                "last_transfer_at": "now()",
            }
        ).eq("id", ticket_id).execute()
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to transfer ticket ownership: {str(e)}")

    try:
        sb.table("ticket_transfer_history").insert(
            {
                "ticket_id": ticket_id,
                "from_user_id": from_internal_user_id,
                "to_user_id": to_user_id,
                "from_wallet_address": from_wallet_address,
                "to_wallet_address": to_wallet_address,
                "transfer_type": "transfer",
                "transfer_status": "completed",
                "risk_level": risk_ctx.get("risk_level"),
                "risk_type": risk_ctx.get("risk_type"),
                "note": note,
            }
        ).execute()
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Ticket ownership changed, but failed to write transfer history. Check ticket_transfer_history table. {str(e)}",
        )

    return {
        "status": "success",
        "message": "Ticket transferred successfully.",
        "ticket_id": ticket_id,
        "from_user_id": from_internal_user_id,
        "to_user_id": to_user_id,
        "risk": {
            "risk_score": risk_ctx["risk_score"],
            "risk_level": risk_ctx["risk_level"],
            "risk_type": risk_ctx["risk_type"],
            "reasons": risk_ctx["reasons"],
            "recommended_action": risk_ctx["recommended_action"],
        },
    }