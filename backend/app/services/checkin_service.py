from datetime import datetime
from fastapi import HTTPException

from app.services.rewards_service import handle_event_checkin_reward
from app.services.risk_service import (
    evaluate_risk_context,
    should_block_checkin,
    should_require_manual_review_for_checkin,
    build_risk_restriction_message,
)


def validate_checkin_risk(
    sb,
    user_id: str | None,
    ticket_id: str | None,
    device_id: str | None = None,
    ip_address: str | None = None,
    risk_overrides: dict | None = None,
):
    payload = {
        "user_id": user_id,
        "ticket_id": ticket_id,
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

    if should_block_checkin(risk_ctx):
        raise HTTPException(
            status_code=403,
            detail={
                "message": build_risk_restriction_message("checkin", lang="en"),
                "risk_level": risk_ctx["risk_level"],
                "risk_type": risk_ctx["risk_type"],
                "reasons": risk_ctx["reasons"],
                "recommended_action": risk_ctx["recommended_action"],
            },
        )

    return risk_ctx


def _insert_checkin_log(
    sb,
    ticket_id: str | None,
    scanned_by: str | None,
    scanner_device_id: str | None,
    scanned_qr_token: str | None,
    result: str,
    note: str | None = None,
):
    sb.table("check_in_logs").insert({
        "ticket_id": ticket_id,
        "scanned_by": scanned_by,
        "scanner_device_id": scanner_device_id,
        "scanned_qr_token": scanned_qr_token,
        "scanned_at": datetime.utcnow().isoformat(),
        "result": result,
        "note": note,
    }).execute()


def check_in_ticket_service(
    sb,
    ticket_id: str,
    scanned_by: str | None = None,
    scanner_device_id: str | None = None,
    scanned_qr_token: str | None = None,
    note: str | None = None,
    ip_address: str | None = None,
    risk_overrides: dict | None = None,
    simulate_only: bool = False,
):
    res = (
        sb.table("tickets")
        .select("*")
        .eq("id", ticket_id)
        .limit(1)
        .execute()
    )

    if not res.data:
        _insert_checkin_log(
            sb=sb,
            ticket_id=None,
            scanned_by=scanned_by,
            scanner_device_id=scanner_device_id,
            scanned_qr_token=scanned_qr_token,
            result="invalid",
            note="ticket not found",
        )
        raise HTTPException(status_code=404, detail="Ticket not found")

    ticket = res.data[0]

    risk_ctx = validate_checkin_risk(
        sb=sb,
        user_id=ticket.get("user_id"),
        ticket_id=ticket_id,
        device_id=scanner_device_id,
        ip_address=ip_address,
        risk_overrides=risk_overrides,
    )

    review_required = should_require_manual_review_for_checkin(risk_ctx)

    if ticket["status"] == "used":
        _insert_checkin_log(
            sb=sb,
            ticket_id=ticket_id,
            scanned_by=scanned_by,
            scanner_device_id=scanner_device_id,
            scanned_qr_token=scanned_qr_token,
            result="duplicate",
            note=note or "ticket already used",
        )
        raise HTTPException(status_code=400, detail="Ticket already used")

    if ticket["status"] != "active":
        _insert_checkin_log(
            sb=sb,
            ticket_id=ticket_id,
            scanned_by=scanned_by,
            scanner_device_id=scanner_device_id,
            scanned_qr_token=scanned_qr_token,
            result="blocked",
            note=note or f"ticket status is {ticket['status']}",
        )
        raise HTTPException(status_code=400, detail="Ticket is not active")

    if simulate_only:
        return {
            "ticket_id": ticket_id,
            "status": ticket["status"],
            "result": "simulated",
            "review_required": review_required,
            "risk": {
                "risk_score": risk_ctx["risk_score"],
                "risk_level": risk_ctx["risk_level"],
                "risk_type": risk_ctx["risk_type"],
                "reasons": risk_ctx["reasons"],
                "recommended_action": risk_ctx["recommended_action"],
            },
        }

    (
        sb.table("tickets")
        .update({"status": "used"})
        .eq("id", ticket_id)
        .execute()
    )

    _insert_checkin_log(
        sb=sb,
        ticket_id=ticket_id,
        scanned_by=scanned_by,
        scanner_device_id=scanner_device_id,
        scanned_qr_token=scanned_qr_token,
        result="success",
        note=note,
    )

    try:
        if ticket.get("user_id"):
            handle_event_checkin_reward(
                sb=sb,
                user_id=ticket["user_id"],
                ticket_id=ticket_id,
            )
    except Exception:
        pass

    return {
        "ticket_id": ticket_id,
        "status": "used",
        "result": "success",
        "review_required": review_required,
        "risk": {
            "risk_score": risk_ctx["risk_score"],
            "risk_level": risk_ctx["risk_level"],
            "risk_type": risk_ctx["risk_type"],
            "reasons": risk_ctx["reasons"],
            "recommended_action": risk_ctx["recommended_action"],
        },
    }