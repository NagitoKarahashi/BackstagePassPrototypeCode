from fastapi import APIRouter, Depends
from pydantic import BaseModel
from supabase import Client

from app.core.deps import supabase_dep, current_user_dep
from app.schemas.profiles import (
    ProfileCreateRequest,
    ProfileUpdateRequest,
)
from app.services.profiles_service import (
    create_profile_service,
    get_profile_service,
    get_profile_by_internal_id_service,
    update_profile_service,
    upsert_profile_service,
    update_wallet_address_service,
)

router = APIRouter(prefix="/profiles", tags=["profiles"])


class WalletAddressUpdateRequest(BaseModel):
    wallet_address: str


@router.post("")
def create_profile(
    payload: ProfileCreateRequest,
    sb: Client = Depends(supabase_dep),
):
    return create_profile_service(sb, payload.model_dump())


@router.post("/upsert")
def upsert_profile(
    payload: ProfileCreateRequest,
    sb: Client = Depends(supabase_dep),
):
    return upsert_profile_service(sb, payload.model_dump())


@router.post("/bootstrap")
def bootstrap_profile(
    current_user=Depends(current_user_dep),
    sb: Client = Depends(supabase_dep),
):
    user_metadata = getattr(current_user, "user_metadata", {}) or {}
    email = getattr(current_user, "email", None)
    wallet_address = getattr(current_user, "wallet_address", None)

    display_name = (
        user_metadata.get("full_name")
        or user_metadata.get("name")
        or email
    )

    username = (
        user_metadata.get("preferred_username")
        or user_metadata.get("username")
        or email
    )

    payload = {
        "external_auth_id": current_user.id,
        "email": email,
        "wallet_address": wallet_address,
        "display_name": display_name,
        "username": username,
    }

    return upsert_profile_service(sb, payload)


@router.get("/me")
def get_my_profile(
    current_user=Depends(current_user_dep),
    sb: Client = Depends(supabase_dep),
):
    return get_profile_service(sb, current_user.id)


@router.patch("/me")
def update_my_profile(
    payload: ProfileUpdateRequest,
    current_user=Depends(current_user_dep),
    sb: Client = Depends(supabase_dep),
):
    return update_profile_service(sb, current_user.id, payload.model_dump())


@router.patch("/me/wallet")
def update_my_wallet(
    payload: WalletAddressUpdateRequest,
    current_user=Depends(current_user_dep),
    sb: Client = Depends(supabase_dep),
):
    return update_wallet_address_service(sb, current_user.id, payload.wallet_address)


@router.get("/{user_id}")
def get_profile(user_id: str, sb: Client = Depends(supabase_dep)):
    return get_profile_by_internal_id_service(sb, user_id)


@router.patch("/{user_id}")
def update_profile(
    user_id: str,
    payload: ProfileUpdateRequest,
    sb: Client = Depends(supabase_dep),
):
    existing = get_profile_by_internal_id_service(sb, user_id)
    resp = (
        sb.table("profiles")
        .update({k: v for k, v in payload.model_dump().items() if v is not None})
        .eq("id", existing["id"])
        .execute()
    )
    return resp.data[0] if resp.data else existing