from fastapi import APIRouter, Depends, Query
from supabase import Client

from app.core.deps import supabase_dep, current_user_dep
from app.services.me_service import (
    get_me_overview_service,
    get_me_history_service,
)

router = APIRouter(prefix="/me", tags=["me"])


@router.get("/overview")
def get_me_overview(
    current_user=Depends(current_user_dep),
    sb: Client = Depends(supabase_dep),
):
    return get_me_overview_service(sb, current_user.id)


@router.get("/history")
def get_me_history(
    current_user=Depends(current_user_dep),
    order_limit: int = Query(default=20, ge=1, le=100),
    ticket_limit: int = Query(default=20, ge=1, le=100),
    sb: Client = Depends(supabase_dep),
):
    return get_me_history_service(
        sb,
        current_user.id,
        order_limit=order_limit,
        ticket_limit=ticket_limit,
    )