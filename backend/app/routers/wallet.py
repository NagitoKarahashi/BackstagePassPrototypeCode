from fastapi import APIRouter, Depends, HTTPException
from supabase import Client

from app.core.deps import supabase_dep, current_user_dep
from app.services.wallet_service import (
    get_wallet_me_service,
    get_wallet_tickets_service,
    get_wallet_ticket_detail_service,
)

router = APIRouter(prefix="/wallet", tags=["wallet"])


@router.get("/me")
def get_wallet_me(
    sb: Client = Depends(supabase_dep),
    current_user=Depends(current_user_dep),
):
    return get_wallet_me_service(sb, str(current_user.id))


@router.get("/tickets")
def get_wallet_tickets(
    sb: Client = Depends(supabase_dep),
    current_user=Depends(current_user_dep),
):
    return get_wallet_tickets_service(sb, str(current_user.id))


@router.get("/tickets/{ticket_id}")
def get_wallet_ticket_detail(
    ticket_id: str,
    sb: Client = Depends(supabase_dep),
    current_user=Depends(current_user_dep),
):
    item = get_wallet_ticket_detail_service(sb, str(current_user.id), ticket_id)
    if not item:
        raise HTTPException(status_code=404, detail="Wallet ticket not found")
    return {"ticket": item}