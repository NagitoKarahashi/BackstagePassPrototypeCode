from datetime import datetime
from fastapi import HTTPException
import time

from app.services.profiles_service import resolve_internal_user_id

MOCK_CONTRACT_ADDRESS = "0xDEADBEEFDEADBEEFDEADBEEFDEADBEEFDEAD0001"
MOCK_CHAIN = "Polygon Amoy"


def _now_iso() -> str:
    return datetime.utcnow().isoformat()


def _mock_tx_hash(seed: str) -> str:
    return f"0xmockmint{seed.replace('-', '')[:24]}"


def _mock_token_id(ticket_id: str) -> str:
    return ticket_id.replace("-", "")[:16]


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


def _get_ticket_or_404(sb, ticket_id: str):
    try:
        ticket_resp = _retry_execute(
            sb.table("tickets")
            .select(
                "id, user_id, status, token_id, contract_address, chain, "
                "owner_wallet, mint_status, minted_at, tx_hash, metadata_uri"
            )
            .eq("id", ticket_id)
            .limit(1),
            retries=1,
        )
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail=f"Ticket lookup temporarily unavailable: {str(e)}",
        )

    if not ticket_resp.data:
        raise HTTPException(status_code=404, detail="Ticket not found")

    return ticket_resp.data[0]


def mint_ticket_service(sb, external_auth_id: str, ticket_id: str):
    internal_user_id = resolve_internal_user_id(sb, external_auth_id)
    ticket = _get_ticket_or_404(sb, ticket_id)

    if ticket.get("user_id") != internal_user_id:
        raise HTTPException(status_code=403, detail="You do not own this ticket")

    if ticket.get("status") != "active":
        raise HTTPException(status_code=400, detail="Only active tickets can be minted")

    if ticket.get("mint_status") == "minted":
        return {
            "ticket_id": ticket["id"],
            "mint_status": "minted",
            "token_id": ticket.get("token_id"),
            "contract_address": ticket.get("contract_address"),
            "chain": ticket.get("chain"),
            "owner_wallet": ticket.get("owner_wallet"),
            "tx_hash": ticket.get("tx_hash"),
            "minted_at": ticket.get("minted_at"),
            "already_minted": True,
        }

    wallet_address = _get_profile_wallet(sb, internal_user_id)
    now = _now_iso()
    tx_hash = _mock_tx_hash(ticket_id)
    token_id = ticket.get("token_id") or _mock_token_id(ticket_id)

    try:
        update_resp = _retry_execute(
            sb.table("tickets")
            .update(
                {
                    "mint_status": "minted",
                    "minted_at": now,
                    "tx_hash": tx_hash,
                    "token_id": token_id,
                    "contract_address": ticket.get("contract_address") or MOCK_CONTRACT_ADDRESS,
                    "chain": ticket.get("chain") or MOCK_CHAIN,
                    "owner_wallet": wallet_address,
                }
            )
            .eq("id", ticket_id)
            .eq("user_id", internal_user_id),
            retries=1,
        )
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail=f"Mint update temporarily unavailable: {str(e)}",
        )

    updated = update_resp.data[0] if update_resp.data else None
    if not updated:
        raise HTTPException(status_code=400, detail="Mint update did not modify the ticket record")

    if (updated.get("mint_status") or "").lower() != "minted":
        raise HTTPException(
            status_code=400,
            detail="Mint update completed but ticket is not marked as minted",
        )

    try:
        _retry_execute(
            sb.table("ticket_ownership_logs").insert(
                {
                    "ticket_id": ticket_id,
                    "from_user_id": None,
                    "to_user_id": internal_user_id,
                    "from_wallet": None,
                    "to_wallet": wallet_address,
                    "action": "mint",
                    "tx_hash": tx_hash,
                    "note": "Mock NFT mint completed",
                }
            ),
            retries=1,
        )
    except Exception:
        pass

    return {
        "ticket_id": ticket_id,
        "mint_status": updated.get("mint_status"),
        "token_id": updated.get("token_id"),
        "contract_address": updated.get("contract_address"),
        "chain": updated.get("chain"),
        "owner_wallet": updated.get("owner_wallet"),
        "tx_hash": updated.get("tx_hash"),
        "minted_at": updated.get("minted_at"),
        "already_minted": False,
    }


def get_ticket_history_service(sb, external_auth_id: str, ticket_id: str):
    internal_user_id = resolve_internal_user_id(sb, external_auth_id)
    ticket = _get_ticket_or_404(sb, ticket_id)

    if ticket.get("user_id") != internal_user_id:
        raise HTTPException(status_code=403, detail="You do not own this ticket")

    try:
        resp = _retry_execute(
            sb.table("ticket_ownership_logs")
            .select("*")
            .eq("ticket_id", ticket_id)
            .order("created_at", desc=False),
            retries=1,
        )
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail=f"Ticket history temporarily unavailable: {str(e)}",
        )

    return {"items": resp.data or []}