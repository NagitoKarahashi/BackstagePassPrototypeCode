from fastapi import APIRouter, Depends
from supabase import Client

from app.core.deps import supabase_dep, current_user_dep
from app.services.web3_service import (
    mint_ticket_service,
    get_ticket_history_service,
)

router = APIRouter(prefix="/web3", tags=["web3"])


@router.post("/tickets/{ticket_id}/mint")
def mint_ticket(
    ticket_id: str,
    sb: Client = Depends(supabase_dep),
    current_user=Depends(current_user_dep),
):
    return mint_ticket_service(
        sb=sb,
        external_auth_id=current_user.id,
        ticket_id=ticket_id,
    )


@router.get("/tickets/{ticket_id}/history")
def get_ticket_history(
    ticket_id: str,
    sb: Client = Depends(supabase_dep),
    current_user=Depends(current_user_dep),
):
    return get_ticket_history_service(
        sb=sb,
        external_auth_id=current_user.id,
        ticket_id=ticket_id,
    )