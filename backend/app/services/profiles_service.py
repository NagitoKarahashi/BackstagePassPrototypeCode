from datetime import datetime, timezone

from fastapi import HTTPException
from supabase import Client

PROFILE_SELECT = """
id,
external_auth_id,
display_name,
email,
wallet_address,
created_at,
username,
avatar_url,
bio,
city,
preferred_genres,
preferred_artists,
fan_points,
following_count,
follower_count,
last_active_at
"""


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _clean_display_name(value: str | None) -> str | None:
    if not value:
        return None
    value = value.strip()
    if not value:
        return None
    if value.startswith("did:privy:"):
        return None
    return value


def _clean_username(value: str | None) -> str | None:
    if not value:
        return None
    value = value.strip()
    if not value:
        return None
    if value.startswith("did:privy:"):
        return None
    return value


def create_profile_service(sb: Client, payload: dict):
    try:
        resp = sb.table("profiles").insert(payload).execute()
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Profile service temporarily unavailable: {e}")

    if not resp.data:
        raise HTTPException(status_code=400, detail="Failed to create profile")

    return resp.data[0]


def get_profile_service(sb: Client, external_auth_id: str):
    try:
        res = (
            sb.table("profiles")
            .select(PROFILE_SELECT)
            .eq("external_auth_id", external_auth_id)
            .limit(1)
            .execute()
        )
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Profile service temporarily unavailable: {e}")

    if not res.data:
        raise HTTPException(status_code=404, detail="Profile not found")
    return res.data[0]


def get_profile_by_internal_id_service(sb: Client, profile_id: str):
    try:
        res = (
            sb.table("profiles")
            .select(PROFILE_SELECT)
            .eq("id", profile_id)
            .limit(1)
            .execute()
        )
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Profile service temporarily unavailable: {e}")

    if not res.data:
        raise HTTPException(status_code=404, detail="Profile not found")
    return res.data[0]


def update_profile_service(sb: Client, external_auth_id: str, payload: dict):
    clean_payload = {k: v for k, v in payload.items() if v is not None}

    if "display_name" in clean_payload:
        clean_payload["display_name"] = _clean_display_name(clean_payload.get("display_name"))
        if clean_payload["display_name"] is None:
            clean_payload.pop("display_name", None)

    if "username" in clean_payload:
        clean_payload["username"] = _clean_username(clean_payload.get("username"))
        if clean_payload["username"] is None:
            clean_payload.pop("username", None)

    try:
        existing = (
            sb.table("profiles")
            .select("id")
            .eq("external_auth_id", external_auth_id)
            .limit(1)
            .execute()
        )
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Profile service temporarily unavailable: {e}")

    if not existing.data:
        raise HTTPException(status_code=404, detail="Profile not found")

    profile_id = existing.data[0]["id"]

    if not clean_payload:
        return get_profile_by_internal_id_service(sb, profile_id)

    try:
        resp = (
            sb.table("profiles")
            .update(clean_payload)
            .eq("id", profile_id)
            .execute()
        )
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Profile update temporarily unavailable: {e}")

    if not resp.data:
        raise HTTPException(status_code=404, detail="Profile not found or not updated")

    return resp.data[0]


def update_wallet_address_service(sb: Client, external_auth_id: str, wallet_address: str):
    wallet_address = (wallet_address or "").strip()
    if not wallet_address:
        raise HTTPException(status_code=400, detail="wallet_address is required")

    try:
        existing = (
            sb.table("profiles")
            .select("id")
            .eq("external_auth_id", external_auth_id)
            .limit(1)
            .execute()
        )
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Profile service temporarily unavailable: {e}")

    if not existing.data:
        raise HTTPException(status_code=404, detail="Profile not found")

    profile_id = existing.data[0]["id"]

    try:
        resp = (
            sb.table("profiles")
            .update(
                {
                    "wallet_address": wallet_address,
                    "last_active_at": _now_iso(),
                }
            )
            .eq("id", profile_id)
            .execute()
        )
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Wallet update temporarily unavailable: {e}")

    if not resp.data:
        raise HTTPException(status_code=400, detail="Failed to update wallet address")

    return resp.data[0]


def upsert_profile_service(sb: Client, payload: dict):
    external_auth_id = payload["external_auth_id"]

    try:
        existing_res = (
            sb.table("profiles")
            .select(PROFILE_SELECT)
            .eq("external_auth_id", external_auth_id)
            .limit(1)
            .execute()
        )
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Profile service temporarily unavailable: {e}")

    incoming_display_name = _clean_display_name(payload.get("display_name"))
    incoming_username = _clean_username(payload.get("username"))

    if existing_res.data:
        existing = existing_res.data[0]
        profile_id = existing["id"]

        update_payload = {
            "email": payload.get("email") if payload.get("email") is not None else existing.get("email"),
            "wallet_address": payload.get("wallet_address") if payload.get("wallet_address") is not None else existing.get("wallet_address"),
            "last_active_at": payload.get("last_active_at") or _now_iso(),
            "display_name": existing.get("display_name") or incoming_display_name,
            "username": existing.get("username") or incoming_username,
        }

        update_payload = {k: v for k, v in update_payload.items() if v is not None}

        try:
            res = (
                sb.table("profiles")
                .update(update_payload)
                .eq("id", profile_id)
                .execute()
            )
        except Exception as e:
            raise HTTPException(status_code=503, detail=f"Profile update temporarily unavailable: {e}")

        if not res.data:
            raise HTTPException(status_code=400, detail="Failed to update profile")
        return res.data[0]

    insert_payload = {
        "external_auth_id": external_auth_id,
        "email": payload.get("email"),
        "wallet_address": payload.get("wallet_address"),
        "display_name": incoming_display_name,
        "username": incoming_username,
        "last_active_at": payload.get("last_active_at") or _now_iso(),
    }

    insert_payload = {k: v for k, v in insert_payload.items() if v is not None}

    try:
        res = sb.table("profiles").insert(insert_payload).execute()
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Profile insert temporarily unavailable: {e}")

    if not res.data:
        raise HTTPException(status_code=400, detail="Failed to insert profile")
    return res.data[0]


def resolve_internal_user_id(sb: Client, external_auth_id: str) -> str:
    try:
        res = (
            sb.table("profiles")
            .select("id")
            .eq("external_auth_id", external_auth_id)
            .limit(1)
            .execute()
        )
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Profile lookup temporarily unavailable: {e}")

    if not res.data:
        raise HTTPException(status_code=404, detail="Profile not found")
    return res.data[0]["id"]