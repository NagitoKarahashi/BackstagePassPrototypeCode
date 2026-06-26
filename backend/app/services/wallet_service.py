from fastapi import HTTPException
import time

from app.services.profiles_service import resolve_internal_user_id


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


def _get_profile_wallet(sb, internal_user_id: str) -> str | None:
    try:
        profile_resp = _retry_execute(
            sb.table("profiles")
            .select("id, wallet_address")
            .eq("id", internal_user_id)
            .limit(1),
            retries=1,
        )
        if not profile_resp.data:
            return None
        return profile_resp.data[0].get("wallet_address")
    except Exception:
        return None


def _get_active_listing_map(sb, ticket_ids: list[str]) -> dict[str, dict]:
    if not ticket_ids:
        return {}

    try:
        listings_resp = _retry_execute(
            sb.table("marketplace_listings")
            .select("id, ticket_id, listing_price, currency, status, created_at, sold_at, cancelled_at")
            .in_("ticket_id", ticket_ids)
            .eq("status", "active"),
            retries=1,
        )
    except Exception:
        return {}

    listing_map: dict[str, dict] = {}
    for row in (listings_resp.data or []):
        ticket_id = row.get("ticket_id")
        if ticket_id and ticket_id not in listing_map:
            listing_map[ticket_id] = row
    return listing_map


def _repair_stale_ticket_flags(sb, ticket_id: str):
    try:
        _retry_execute(
            sb.table("tickets")
            .update(
                {
                    "is_listed": False,
                    "transfer_locked": False,
                }
            )
            .eq("id", ticket_id),
            retries=1,
        )
    except Exception:
        pass


def get_wallet_me_service(sb, external_auth_id: str):
    internal_user_id = resolve_internal_user_id(sb, external_auth_id)
    wallet_address = _get_profile_wallet(sb, internal_user_id)

    try:
        tickets_resp = _retry_execute(
            sb.table("tickets")
            .select("id, mint_status")
            .eq("user_id", internal_user_id),
            retries=1,
        )
        tickets = tickets_resp.data or []
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail=f"Wallet tickets temporarily unavailable: {str(e)}",
        )

    ticket_ids = [t["id"] for t in tickets if t.get("id")]
    active_listing_map = _get_active_listing_map(sb, ticket_ids)

    minted_count = len([t for t in tickets if (t.get("mint_status") or "").lower() == "minted"])
    listed_count = len(active_listing_map)

    return {
        "wallet_address": wallet_address,
        "total_tickets": len(tickets),
        "minted_tickets": minted_count,
        "listed_tickets": listed_count,
    }


def get_wallet_tickets_service(sb, external_auth_id: str):
    internal_user_id = resolve_internal_user_id(sb, external_auth_id)

    try:
        tickets_resp = _retry_execute(
            sb.table("tickets")
            .select(
                "id, order_id, event_id, event_uuid, token_id, contract_address, chain, "
                "metadata, metadata_uri, qr_payload, status, created_at, owner_wallet, "
                "mint_status, minted_at, tx_hash, is_listed, transfer_locked"
            )
            .eq("user_id", internal_user_id)
            .order("created_at", desc=True),
            retries=1,
        )
        tickets = tickets_resp.data or []
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail=f"Wallet ticket list temporarily unavailable: {str(e)}",
        )

    ticket_ids = [t["id"] for t in tickets if t.get("id")]
    active_listing_map = _get_active_listing_map(sb, ticket_ids)

    event_ids = [t["event_uuid"] for t in tickets if t.get("event_uuid")]
    event_map = {}

    if event_ids:
        try:
            events_resp = _retry_execute(
                sb.table("events")
                .select("id, title, artist, city, genre, start_time, poster_url")
                .in_("id", event_ids),
                retries=1,
            )
            for e in (events_resp.data or []):
                event_map[e["id"]] = e
        except Exception:
            event_map = {}

    items = []
    for t in tickets:
        event = event_map.get(t.get("event_uuid"), {})
        active_listing = active_listing_map.get(t["id"])
        is_actually_listed = active_listing is not None

        # stale flag repair
        if t.get("is_listed") and not is_actually_listed:
            _repair_stale_ticket_flags(sb, t["id"])

        items.append(
            {
                "id": t.get("id"),
                "order_id": t.get("order_id"),
                "event_id": t.get("event_id"),
                "event_uuid": t.get("event_uuid"),
                "title": event.get("title"),
                "artist": event.get("artist"),
                "city": event.get("city"),
                "genre": event.get("genre"),
                "start_time": event.get("start_time"),
                "poster_url": event.get("poster_url"),
                "status": t.get("status"),
                "token_id": t.get("token_id"),
                "contract_address": t.get("contract_address"),
                "chain": t.get("chain"),
                "owner_wallet": t.get("owner_wallet"),
                "mint_status": t.get("mint_status") or "not_minted",
                "minted_at": t.get("minted_at"),
                "tx_hash": t.get("tx_hash"),
                "metadata_uri": t.get("metadata_uri"),
                "metadata": t.get("metadata"),
                "is_listed": is_actually_listed,
                "transfer_locked": bool(t.get("transfer_locked")) if is_actually_listed else False,
                "active_listing": active_listing,
                "created_at": t.get("created_at"),
            }
        )

    return {"items": items}


def get_wallet_ticket_detail_service(sb, external_auth_id: str, ticket_id: str):
    internal_user_id = resolve_internal_user_id(sb, external_auth_id)

    try:
        ticket_resp = _retry_execute(
            sb.table("tickets")
            .select(
                "id, order_id, event_id, event_uuid, token_id, contract_address, chain, "
                "metadata, metadata_uri, qr_payload, status, created_at, owner_wallet, "
                "mint_status, minted_at, tx_hash, is_listed, transfer_locked, user_id"
            )
            .eq("id", ticket_id)
            .limit(1),
            retries=1,
        )
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail=f"Wallet ticket detail temporarily unavailable: {str(e)}",
        )

    if not ticket_resp.data:
        return None

    ticket = ticket_resp.data[0]
    if ticket.get("user_id") != internal_user_id:
        return None

    event = {}
    if ticket.get("event_uuid"):
        try:
            event_resp = _retry_execute(
                sb.table("events")
                .select("id, title, artist, city, genre, start_time, poster_url, description")
                .eq("id", ticket["event_uuid"])
                .limit(1),
                retries=1,
            )
            event = event_resp.data[0] if event_resp.data else {}
        except Exception:
            event = {}

    active_listing = None
    try:
        listing_resp = _retry_execute(
            sb.table("marketplace_listings")
            .select("id, listing_price, currency, status, created_at, sold_at, cancelled_at")
            .eq("ticket_id", ticket_id)
            .eq("status", "active")
            .limit(1),
            retries=1,
        )
        active_listing = listing_resp.data[0] if listing_resp.data else None
    except Exception:
        active_listing = None

    is_actually_listed = active_listing is not None

    if ticket.get("is_listed") and not is_actually_listed:
        _repair_stale_ticket_flags(sb, ticket_id)

    return {
        "id": ticket.get("id"),
        "order_id": ticket.get("order_id"),
        "event_id": ticket.get("event_id"),
        "event_uuid": ticket.get("event_uuid"),
        "title": event.get("title"),
        "artist": event.get("artist"),
        "city": event.get("city"),
        "genre": event.get("genre"),
        "start_time": event.get("start_time"),
        "poster_url": event.get("poster_url"),
        "description": event.get("description"),
        "status": ticket.get("status"),
        "token_id": ticket.get("token_id"),
        "contract_address": ticket.get("contract_address"),
        "chain": ticket.get("chain"),
        "owner_wallet": ticket.get("owner_wallet"),
        "mint_status": ticket.get("mint_status") or "not_minted",
        "minted_at": ticket.get("minted_at"),
        "tx_hash": ticket.get("tx_hash"),
        "metadata_uri": ticket.get("metadata_uri"),
        "metadata": ticket.get("metadata"),
        "is_listed": is_actually_listed,
        "transfer_locked": bool(ticket.get("transfer_locked")) if is_actually_listed else False,
        "active_listing": active_listing,
        "created_at": ticket.get("created_at"),
    }