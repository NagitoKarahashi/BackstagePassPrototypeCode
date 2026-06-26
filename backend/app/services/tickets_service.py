from fastapi import HTTPException
import time

from app.services.refund_service import request_refund_service
from app.services.profiles_service import resolve_internal_user_id


TICKET_SELECT = """
id,
user_id,
order_id,
event_id,
event_uuid,
token_id,
contract_address,
chain,
metadata,
qr_payload,
status,
is_listed,
transfer_locked,
resale_allowed,
last_transfer_at,
created_at,
owner_wallet,
mint_status,
minted_at,
tx_hash,
metadata_uri
"""

EVENT_SELECT = """
id,
event_code,
title,
artist,
genre,
city,
start_time,
poster_url
"""

LISTING_SELECT = """
id,
ticket_id,
seller_user_id,
buyer_user_id,
listing_price,
currency,
status,
expires_at,
sold_at,
cancelled_at,
created_at,
tx_hash
"""

TRANSFER_HISTORY_SELECT = """
id,
ticket_id,
from_user_id,
to_user_id,
from_wallet_address,
to_wallet_address,
transfer_type,
transfer_status,
risk_level,
risk_type,
note,
created_at
"""


def _retry_execute(builder, retries: int = 1, delay: float = 0.25):
    last_error = None
    for attempt in range(retries + 1):
        try:
            return builder.execute()
        except Exception as e:
            last_error = e
            if attempt < retries:
                time.sleep(delay)
            else:
                raise last_error


def get_user_tickets_service(sb, external_auth_id: str):
    internal_user_id = resolve_internal_user_id(sb, external_auth_id)

    try:
        res = _retry_execute(
            sb.table("tickets")
            .select(TICKET_SELECT)
            .eq("user_id", internal_user_id)
            .order("created_at", desc=True),
            retries=1,
        )
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Ticket service temporarily unavailable: {e}")

    return {"items": res.data or []}


def get_ticket_by_id_service(sb, ticket_id: str):
    try:
        res = _retry_execute(
            sb.table("tickets")
            .select(TICKET_SELECT)
            .eq("id", ticket_id)
            .limit(1),
            retries=1,
        )
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Ticket detail temporarily unavailable: {e}")

    if not res.data:
        raise HTTPException(status_code=404, detail="Ticket not found")

    ticket = res.data[0]

    event_brief = None
    if ticket.get("event_uuid"):
        try:
            event_res = _retry_execute(
                sb.table("events")
                .select(EVENT_SELECT)
                .eq("id", ticket["event_uuid"])
                .limit(1),
                retries=1,
            )
            if event_res.data:
                event_brief = event_res.data[0]
        except Exception:
            event_brief = None

    current_listing = None
    if ticket.get("is_listed"):
        try:
            listing_res = _retry_execute(
                sb.table("marketplace_listings")
                .select(LISTING_SELECT)
                .eq("ticket_id", ticket_id)
                .eq("status", "active")
                .order("created_at", desc=True)
                .limit(1),
                retries=1,
            )
            if listing_res.data:
                current_listing = listing_res.data[0]
        except Exception:
            current_listing = None

    history_preview = []
    try:
        history_res = _retry_execute(
            sb.table("ticket_transfer_history")
            .select(TRANSFER_HISTORY_SELECT)
            .eq("ticket_id", ticket_id)
            .order("created_at", desc=False)
            .limit(5),
            retries=1,
        )
        history_preview = history_res.data or []
    except Exception:
        history_preview = []

    return {
        "ticket": ticket,
        "event": event_brief,
        "current_listing": current_listing,
        "history_preview": history_preview,
    }


def get_ticket_qr_service(sb, ticket_id: str):
    try:
        res = _retry_execute(
            sb.table("tickets")
            .select("id, qr_payload, status")
            .eq("id", ticket_id)
            .limit(1),
            retries=1,
        )
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Ticket QR temporarily unavailable: {e}")

    if not res.data:
        raise HTTPException(status_code=404, detail="Ticket not found")

    ticket = res.data[0]

    if ticket["status"] != "active":
        return {
            "ticket_id": ticket["id"],
            "status": ticket["status"],
            "qr_payload": None,
        }

    return {
        "ticket_id": ticket["id"],
        "status": ticket["status"],
        "qr_payload": ticket["qr_payload"],
    }


def get_tickets_by_order_service(sb, order_id: str):
    try:
        res = _retry_execute(
            sb.table("tickets")
            .select(TICKET_SELECT)
            .eq("order_id", order_id)
            .order("created_at", desc=False),
            retries=1,
        )
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Order tickets temporarily unavailable: {e}")

    return {"items": res.data or []}


def get_ticket_history_service(sb, ticket_id: str):
    try:
        ticket_res = _retry_execute(
            sb.table("tickets")
            .select("id")
            .eq("id", ticket_id)
            .limit(1),
            retries=1,
        )
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Ticket history temporarily unavailable: {e}")

    if not ticket_res.data:
        raise HTTPException(status_code=404, detail="Ticket not found")

    try:
        history_res = _retry_execute(
            sb.table("ticket_transfer_history")
            .select(TRANSFER_HISTORY_SELECT)
            .eq("ticket_id", ticket_id)
            .order("created_at", desc=False),
            retries=1,
        )
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail=f"Ticket history temporarily unavailable: {e}",
        )

    return {"items": history_res.data or []}


def get_ticket_market_status_service(sb, ticket_id: str):
    try:
        ticket_res = _retry_execute(
            sb.table("tickets")
            .select(
                "id, is_listed, transfer_locked, resale_allowed, owner_wallet, "
                "mint_status, token_id, contract_address, chain, tx_hash, status"
            )
            .eq("id", ticket_id)
            .limit(1),
            retries=1,
        )
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail=f"Ticket market status temporarily unavailable: {e}",
        )

    if not ticket_res.data:
        raise HTTPException(status_code=404, detail="Ticket not found")

    ticket = ticket_res.data[0]

    # 永远查 active listing，不再依赖 ticket.is_listed
    try:
        listing_res = _retry_execute(
            sb.table("marketplace_listings")
            .select(LISTING_SELECT)
            .eq("ticket_id", ticket_id)
            .eq("status", "active")
            .order("created_at", desc=True)
            .limit(1),
            retries=1,
        )
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail=f"Marketplace listing lookup temporarily unavailable: {e}",
        )

    listing = listing_res.data[0] if listing_res.data else None
    has_active_listing = listing is not None

    # 用 active listing 作为唯一真相源
    effective_is_listed = has_active_listing
    effective_transfer_locked = has_active_listing

    # 如果 ticket flags 和真实 active listing 不一致，就自动修正
    ticket_flag_is_listed = bool(ticket.get("is_listed"))
    ticket_flag_locked = bool(ticket.get("transfer_locked"))

    if ticket_flag_is_listed != effective_is_listed or ticket_flag_locked != effective_transfer_locked:
        try:
            _retry_execute(
                sb.table("tickets")
                .update(
                    {
                        "is_listed": effective_is_listed,
                        "transfer_locked": effective_transfer_locked,
                    }
                )
                .eq("id", ticket_id),
                retries=1,
            )
        except Exception:
            pass

    return {
        "ticket_id": ticket_id,
        "ticket_status": ticket.get("status"),
        "is_listed": effective_is_listed,
        "transfer_locked": effective_transfer_locked,
        "resale_allowed": ticket.get("resale_allowed", True),
        "owner_wallet": ticket.get("owner_wallet"),
        "mint_status": ticket.get("mint_status") or "not_minted",
        "token_id": ticket.get("token_id"),
        "contract_address": ticket.get("contract_address"),
        "chain": ticket.get("chain"),
        "tx_hash": ticket.get("tx_hash"),
        "listing": listing,
    }


def refund_ticket_service(
    sb,
    ticket_id: str,
    external_auth_id: str,
    device_id: str | None = None,
    ip_address: str | None = None,
    risk_overrides: dict | None = None,
    simulate_only: bool = False,
):
    internal_user_id = resolve_internal_user_id(sb, external_auth_id)

    try:
        ticket_resp = _retry_execute(
            sb.table("tickets")
            .select("id, user_id, order_id, status, is_listed, transfer_locked")
            .eq("id", ticket_id)
            .limit(1),
            retries=1,
        )
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Refund service temporarily unavailable: {e}")

    ticket = ticket_resp.data[0] if ticket_resp.data else None
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    if str(ticket["user_id"]) != str(internal_user_id):
        raise HTTPException(status_code=403, detail="You do not own this ticket")

    if ticket["status"] in {"used", "expired", "refunded"}:
        raise HTTPException(
            status_code=400,
            detail=f"Ticket in status '{ticket['status']}' cannot be refunded",
        )

    if ticket.get("is_listed"):
        raise HTTPException(
            status_code=400,
            detail="Listed tickets cannot be refunded until the listing is cancelled",
        )

    if ticket.get("transfer_locked"):
        raise HTTPException(
            status_code=400,
            detail="Transfer-locked tickets cannot be refunded right now",
        )

    return request_refund_service(
        sb=sb,
        ticket_id=ticket_id,
        user_id=internal_user_id,
        device_id=device_id,
        ip_address=ip_address,
        risk_overrides=risk_overrides,
        simulate_only=simulate_only,
    )