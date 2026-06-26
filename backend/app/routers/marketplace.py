from fastapi import APIRouter, Depends
from supabase import Client

from app.core.deps import supabase_dep, current_user_dep
from app.schemas.tickets import CreateListingRequest
from app.services.marketplace_service import (
    create_listing_service,
    list_marketplace_items_service,
    list_my_marketplace_items_service,
    get_listing_by_id_service,
    buy_listing_service,
    cancel_listing_service,
)

router = APIRouter(prefix="/market", tags=["marketplace"])


@router.get("/listings")
def list_marketplace_items(sb: Client = Depends(supabase_dep)):
    return list_marketplace_items_service(sb)


@router.get("/my-listings")
def list_my_marketplace_items(
    sb: Client = Depends(supabase_dep),
    current_user=Depends(current_user_dep),
):
    return list_my_marketplace_items_service(
        sb=sb,
        seller_user_id=current_user.id,
    )


@router.get("/listings/{listing_id}")
def get_listing(listing_id: str, sb: Client = Depends(supabase_dep)):
    return get_listing_by_id_service(sb, listing_id)


@router.post("/listings")
def create_listing(
    req: CreateListingRequest,
    sb: Client = Depends(supabase_dep),
    current_user=Depends(current_user_dep),
):
    return create_listing_service(
        sb=sb,
        ticket_id=req.ticket_id,
        seller_user_id=current_user.id,
        listing_price=req.listing_price,
        currency=req.currency,
        expires_at=req.expires_at,
    )


@router.post("/listings/{listing_id}/buy")
def buy_listing(
    listing_id: str,
    sb: Client = Depends(supabase_dep),
    current_user=Depends(current_user_dep),
):
    return buy_listing_service(
        sb=sb,
        listing_id=listing_id,
        buyer_user_id=current_user.id,
    )


@router.post("/listings/{listing_id}/cancel")
def cancel_listing(
    listing_id: str,
    sb: Client = Depends(supabase_dep),
    current_user=Depends(current_user_dep),
):
    return cancel_listing_service(
        sb=sb,
        listing_id=listing_id,
        seller_user_id=current_user.id,
    )