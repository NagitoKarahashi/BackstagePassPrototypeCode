from fastapi import APIRouter, Depends
from supabase import Client

from app.core.deps import supabase_dep, current_user_dep
from app.services.orders_service import (
    create_order_service,
    pay_order_service,
    cancel_order_service,
)
from app.schemas.orders import CreateOrderRequest

router = APIRouter(prefix="/orders", tags=["orders"])


@router.post("/create")
def create_order(
    req: CreateOrderRequest,
    current_user=Depends(current_user_dep),
    sb: Client = Depends(supabase_dep),
):
    return create_order_service(
        sb=sb,
        external_auth_id=current_user.id,
        event_id=req.event_id,
        quantity=req.quantity,
    )


@router.post("/{order_id}/pay")
def pay_order(order_id: str, sb: Client = Depends(supabase_dep)):
    return pay_order_service(sb, order_id)


@router.post("/{order_id}/cancel")
def cancel_order(order_id: str, sb: Client = Depends(supabase_dep)):
    return cancel_order_service(sb, order_id)