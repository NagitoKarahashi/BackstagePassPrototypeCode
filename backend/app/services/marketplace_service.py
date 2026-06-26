from datetime import datetime
from fastapi import HTTPException
import time

from app.services.profiles_service import resolve_internal_user_id
from app.services.risk_service import (
    evaluate_risk_context,
    should_block_transfer_like_action,
)

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


def _now_iso() -> str:
    return datetime.utcnow().isoformat()


def _mock_tx_hash(seed: str) -> str:
    return f"0xmockmarket{seed.replace('-', '')[:24]}"


def _get_profile_wallet(sb, user_id: str) -> str | None:
    try:
        profile_res = _retry_execute(
            sb.table("profiles")
            .select("id, wallet_address")
            .eq("id", user_id)
            .limit(1),
            retries=1,
        )
        if not profile_res.data:
            return None
        return profile_res.data[0].get("wallet_address")
    except Exception:
        return None


def _sync_ticket_listing_flags(sb, ticket_id: str, is_listed: bool, owner_wallet: str | None = None):
    payload = {
        "is_listed": is_listed,
        "transfer_locked": is_listed,
    }
    if owner_wallet is not None:
        payload["owner_wallet"] = owner_wallet

    try:
        _retry_execute(
            sb.table("tickets")
            .update(payload)
            .eq("id", ticket_id),
            retries=1,
        )
    except Exception:
        pass


def _get_ticket_or_404(sb, ticket_id: str):
    try:
        ticket_res = _retry_execute(
            sb.table("tickets")
            .select(
                "id, user_id, status, is_listed, transfer_locked, resale_allowed, "
                "event_uuid, qr_payload, owner_wallet, mint_status, token_id, "
                "contract_address, chain, tx_hash"
            )
            .eq("id", ticket_id)
            .limit(1),
            retries=1,
        )
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Ticket temporarily unavailable: {str(e)}")

    if not ticket_res.data:
        raise HTTPException(status_code=404, detail="Ticket not found")
    return ticket_res.data[0]


def _get_active_listing_for_ticket(sb, ticket_id: str):
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
    except Exception:
        return None
    return listing_res.data[0] if listing_res.data else None


def _attach_listing_ticket_details(sb, listings: list[dict]) -> list[dict]:
    if not listings:
        return []

    ticket_ids = [row["ticket_id"] for row in listings if row.get("ticket_id")]
    ticket_map = {}

    if ticket_ids:
        try:
            tickets_res = _retry_execute(
                sb.table("tickets")
                .select(
                    "id, event_uuid, status, owner_wallet, mint_status, token_id, "
                    "contract_address, chain"
                )
                .in_("id", ticket_ids),
                retries=1,
            )
            for t in (tickets_res.data or []):
                ticket_map[t["id"]] = t
        except Exception:
            ticket_map = {}

    items = []
    for row in listings:
        ticket = ticket_map.get(row.get("ticket_id"), {})
        items.append(
            {
                **row,
                "ticket_status": ticket.get("status"),
                "event_uuid": ticket.get("event_uuid"),
                "owner_wallet": ticket.get("owner_wallet"),
                "mint_status": ticket.get("mint_status"),
                "token_id": ticket.get("token_id"),
                "contract_address": ticket.get("contract_address"),
                "chain": ticket.get("chain"),
            }
        )
    return items


def create_listing_service(
    sb,
    ticket_id: str,
    seller_user_id: str,
    listing_price: float,
    currency: str = "USD",
    expires_at: str | None = None,
):
    seller_internal_user_id = resolve_internal_user_id(sb, seller_user_id)
    ticket = _get_ticket_or_404(sb, ticket_id)

    if ticket["user_id"] != seller_internal_user_id:
        raise HTTPException(status_code=403, detail="You are not the current owner of this ticket")

    if ticket["status"] != "active":
        raise HTTPException(status_code=400, detail="Only active tickets can be listed")

    active_listing = _get_active_listing_for_ticket(sb, ticket_id)

    # stale flag repair: ticket says listed/locked, but no active listing exists
    if not active_listing and (ticket.get("is_listed") or ticket.get("transfer_locked")):
        _sync_ticket_listing_flags(sb, ticket_id, False, ticket.get("owner_wallet"))
        ticket["is_listed"] = False
        ticket["transfer_locked"] = False

    if active_listing:
        raise HTTPException(status_code=400, detail="Ticket already has an active listing")

    if ticket.get("transfer_locked"):
        raise HTTPException(status_code=403, detail="Ticket is transfer locked and cannot be listed")

    if not ticket.get("resale_allowed", True):
        raise HTTPException(status_code=403, detail="This ticket is not allowed for resale")

    seller_wallet = _get_profile_wallet(sb, seller_internal_user_id) or ticket.get("owner_wallet")

    risk_ctx = evaluate_risk_context(
        sb,
        {
            "user_id": seller_internal_user_id,
            "event_uuid": ticket.get("event_uuid"),
            "listing_price": listing_price,
            "transfer_attempts_recent": 1,
        },
        lang="en",
    )

    if should_block_transfer_like_action(risk_ctx):
        raise HTTPException(
            status_code=403,
            detail={
                "message": "Listing is temporarily restricted due to elevated risk signals.",
                "risk_level": risk_ctx["risk_level"],
                "risk_type": risk_ctx["risk_type"],
                "reasons": risk_ctx["reasons"],
                "recommended_action": risk_ctx["recommended_action"],
            },
        )

    try:
        insert_res = _retry_execute(
            sb.table("marketplace_listings")
            .insert(
                {
                    "ticket_id": ticket_id,
                    "seller_user_id": seller_internal_user_id,
                    "listing_price": listing_price,
                    "currency": currency,
                    "status": "active",
                    "expires_at": expires_at,
                }
            ),
            retries=1,
        )
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Failed to create listing. {str(e)}",
        )

    _sync_ticket_listing_flags(sb, ticket_id, True, seller_wallet)

    try:
        _retry_execute(
            sb.table("ticket_transfer_history").insert(
                {
                    "ticket_id": ticket_id,
                    "from_user_id": seller_internal_user_id,
                    "to_user_id": seller_internal_user_id,
                    "from_wallet_address": seller_wallet,
                    "to_wallet_address": seller_wallet,
                    "transfer_type": "listing",
                    "transfer_status": "active",
                    "note": "ticket listed on marketplace",
                }
            ),
            retries=1,
        )
    except Exception:
        pass

    item = insert_res.data[0] if insert_res.data else None
    return {
        "status": "success",
        "listing": {
            **(item or {}),
            "seller_wallet": seller_wallet,
            "mint_status": ticket.get("mint_status"),
            "token_id": ticket.get("token_id"),
            "contract_address": ticket.get("contract_address"),
            "chain": ticket.get("chain"),
        },
        "risk": risk_ctx,
    }


def list_marketplace_items_service(sb):
    try:
        res = _retry_execute(
            sb.table("marketplace_listings")
            .select(LISTING_SELECT)
            .eq("status", "active")
            .order("created_at", desc=True),
            retries=1,
        )
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Failed to load marketplace listings. {str(e)}",
        )

    items = _attach_listing_ticket_details(sb, res.data or [])
    return {"items": items}


def list_my_marketplace_items_service(sb, seller_user_id: str):
    seller_internal_user_id = resolve_internal_user_id(sb, seller_user_id)

    try:
        res = _retry_execute(
            sb.table("marketplace_listings")
            .select(LISTING_SELECT)
            .eq("seller_user_id", seller_internal_user_id)
            .order("created_at", desc=True),
            retries=1,
        )
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Failed to load seller listings. {str(e)}",
        )

    items = _attach_listing_ticket_details(sb, res.data or [])
    return {"items": items}


def get_listing_by_id_service(sb, listing_id: str):
    try:
        res = _retry_execute(
            sb.table("marketplace_listings")
            .select(LISTING_SELECT)
            .eq("id", listing_id)
            .limit(1),
            retries=1,
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to load listing. {str(e)}")

    if not res.data:
        raise HTTPException(status_code=404, detail="Listing not found")

    listing = _attach_listing_ticket_details(sb, res.data)[0]
    return {"listing": listing}


def cancel_listing_service(sb, listing_id: str, seller_user_id: str):
    seller_internal_user_id = resolve_internal_user_id(sb, seller_user_id)

    try:
        listing_res = _retry_execute(
            sb.table("marketplace_listings")
            .select(LISTING_SELECT)
            .eq("id", listing_id)
            .limit(1),
            retries=1,
        )
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Listing temporarily unavailable: {str(e)}")

    if not listing_res.data:
        raise HTTPException(status_code=404, detail="Listing not found")

    listing = listing_res.data[0]

    if listing["seller_user_id"] != seller_internal_user_id:
        raise HTTPException(status_code=403, detail="You are not the seller of this listing")

    if listing["status"] != "active":
        raise HTTPException(status_code=400, detail="Only active listings can be cancelled")

    now = _now_iso()
    seller_wallet = _get_profile_wallet(sb, seller_internal_user_id)

    try:
        _retry_execute(
            sb.table("marketplace_listings")
            .update(
                {
                    "status": "cancelled",
                    "cancelled_at": now,
                }
            )
            .eq("id", listing_id),
            retries=1,
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to cancel listing: {str(e)}")

    _sync_ticket_listing_flags(sb, listing["ticket_id"], False, seller_wallet)

    try:
        _retry_execute(
            sb.table("ticket_transfer_history").insert(
                {
                    "ticket_id": listing["ticket_id"],
                    "from_user_id": seller_internal_user_id,
                    "to_user_id": seller_internal_user_id,
                    "from_wallet_address": seller_wallet,
                    "to_wallet_address": seller_wallet,
                    "transfer_type": "cancel_listing",
                    "transfer_status": "completed",
                    "note": f"listing {listing_id} cancelled",
                }
            ),
            retries=1,
        )
    except Exception:
        pass

    return {
        "status": "success",
        "message": "Listing cancelled successfully",
        "listing_id": listing_id,
    }


def buy_listing_service(sb, listing_id: str, buyer_user_id: str):
    buyer_internal_user_id = resolve_internal_user_id(sb, buyer_user_id)

    try:
        listing_res = _retry_execute(
            sb.table("marketplace_listings")
            .select(LISTING_SELECT)
            .eq("id", listing_id)
            .limit(1),
            retries=1,
        )
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Listing temporarily unavailable: {str(e)}")

    if not listing_res.data:
        raise HTTPException(status_code=404, detail="Listing not found")

    listing = listing_res.data[0]

    if listing["status"] != "active":
        raise HTTPException(status_code=400, detail="Listing is no longer active")

    if listing["seller_user_id"] == buyer_internal_user_id:
        raise HTTPException(status_code=400, detail="Seller cannot buy their own listing")

    ticket = _get_ticket_or_404(sb, listing["ticket_id"])

    if ticket["status"] != "active":
        raise HTTPException(status_code=400, detail="Only active tickets can be purchased")

    if ticket["user_id"] != listing["seller_user_id"]:
        raise HTTPException(status_code=400, detail="Ticket owner does not match listing seller")

    buyer_wallet = _get_profile_wallet(sb, buyer_internal_user_id)
    seller_wallet = _get_profile_wallet(sb, listing["seller_user_id"]) or ticket.get("owner_wallet")
    now = _now_iso()
    tx_hash = _mock_tx_hash(listing_id)

    try:
        # 1) Atomic listing claim:
        # Only one concurrent request can update active -> sold.
        sold_listing_resp = _retry_execute(
            sb.table("marketplace_listings")
            .update(
                {
                    "status": "sold",
                    "buyer_user_id": buyer_internal_user_id,
                    "buyer_wallet": buyer_wallet,
                    "sold_at": now,
                    "tx_hash": tx_hash,
                }
            )
            .eq("id", listing_id)
            .eq("status", "active"),
            retries=1,
        )

        sold_listing_rows = sold_listing_resp.data or []

        if not sold_listing_rows:
            raise HTTPException(
                status_code=400,
                detail="Listing is no longer active",
            )

        listing = sold_listing_rows[0]

        # 2) Ticket owner / flags update:
        # Only update if the seller is still the current owner.
        ticket_update_resp = _retry_execute(
            sb.table("tickets")
            .update(
                {
                    "user_id": buyer_internal_user_id,
                    "owner_wallet": buyer_wallet,
                    "is_listed": False,
                    "transfer_locked": False,
                    "last_transfer_at": now,
                    "tx_hash": tx_hash,
                }
            )
            .eq("id", listing["ticket_id"])
            .eq("user_id", listing["seller_user_id"]),
            retries=1,
        )

        ticket_update_rows = ticket_update_resp.data or []

        if not ticket_update_rows:
            raise HTTPException(
                status_code=409,
                detail="Ticket ownership changed before purchase could be completed",
            )

        # 3) Clean remaining active listings for the same ticket.
        _retry_execute(
            sb.table("marketplace_listings")
            .update(
                {
                    "status": "cancelled",
                    "cancelled_at": now,
                }
            )
            .eq("ticket_id", listing["ticket_id"])
            .eq("status", "active"),
            retries=1,
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to complete listing purchase: {str(e)}")

    # 4) Ops history
    try:
        _retry_execute(
            sb.table("ticket_transfer_history").insert(
                {
                    "ticket_id": listing["ticket_id"],
                    "from_user_id": listing["seller_user_id"],
                    "to_user_id": buyer_internal_user_id,
                    "from_wallet_address": seller_wallet,
                    "to_wallet_address": buyer_wallet,
                    "transfer_type": "resale",
                    "transfer_status": "completed",
                    "note": f"secondary market sale via listing {listing_id}",
                    "tx_hash": tx_hash,
                }
            ),
            retries=1,
        )
    except Exception:
        pass

    # 5) Ownership history
    try:
        _retry_execute(
            sb.table("ticket_ownership_logs").insert(
                {
                    "ticket_id": listing["ticket_id"],
                    "from_user_id": listing["seller_user_id"],
                    "to_user_id": buyer_internal_user_id,
                    "from_wallet": seller_wallet,
                    "to_wallet": buyer_wallet,
                    "action": "resale_purchase",
                    "tx_hash": tx_hash,
                    "note": f"secondary market purchase via listing {listing_id}",
                }
            ),
            retries=1,
        )
    except Exception:
        pass

    return {
        "status": "success",
        "message": "Listing purchased successfully",
        "listing_id": listing_id,
        "ticket_id": listing["ticket_id"],
        "new_owner_user_id": buyer_internal_user_id,
        "buyer_wallet": buyer_wallet,
        "tx_hash": tx_hash,
    }
