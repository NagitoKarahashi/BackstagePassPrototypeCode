from fastapi import APIRouter, Depends
from supabase import Client

from app.core.deps import supabase_dep, current_user_dep
from app.schemas.tickets import (
    TransferTicketRequest,
    RefundTicketRequest,
    RefundTicketResponse,
)
from app.services.tickets_service import (
    get_user_tickets_service,
    get_ticket_by_id_service,
    get_ticket_qr_service,
    get_tickets_by_order_service,
    refund_ticket_service,
    get_ticket_history_service,
    get_ticket_market_status_service,
)
from app.services.transfer_service import request_transfer_service

router = APIRouter(prefix="/tickets", tags=["tickets"])


@router.get("/my")
def my_tickets(
    current_user=Depends(current_user_dep),
    sb: Client = Depends(supabase_dep),
):
    return get_user_tickets_service(sb, current_user.id)


@router.get("/{ticket_id}")
def get_ticket(ticket_id: str, sb: Client = Depends(supabase_dep)):
    return get_ticket_by_id_service(sb, ticket_id)


@router.get("/{ticket_id}/history")
def get_ticket_history(ticket_id: str, sb: Client = Depends(supabase_dep)):
    return get_ticket_history_service(sb, ticket_id)


@router.get("/{ticket_id}/market-status")
def get_ticket_market_status(ticket_id: str, sb: Client = Depends(supabase_dep)):
    return get_ticket_market_status_service(sb, ticket_id)


@router.get("/{ticket_id}/qr")
def get_ticket_qr(ticket_id: str, sb: Client = Depends(supabase_dep)):
    return get_ticket_qr_service(sb, ticket_id)


@router.get("/order/{order_id}")
def get_order_tickets(order_id: str, sb: Client = Depends(supabase_dep)):
    return get_tickets_by_order_service(sb, order_id)


@router.post("/{ticket_id}/transfer")
def transfer_ticket(
    ticket_id: str,
    req: TransferTicketRequest,
    sb: Client = Depends(supabase_dep),
    current_user=Depends(current_user_dep),
):
    return request_transfer_service(
        sb=sb,
        ticket_id=ticket_id,
        from_user_id=current_user.id,
        to_user_id=req.to_user_id,
        to_wallet_address=req.to_wallet_address,
        note=req.note,
        device_id=req.device_id,
        ip_address=req.ip_address,
    )


@router.post("/{ticket_id}/refund", response_model=RefundTicketResponse)
def refund_ticket(
    ticket_id: str,
    req: RefundTicketRequest,
    sb: Client = Depends(supabase_dep),
    current_user=Depends(current_user_dep),
):
    return refund_ticket_service(
        sb=sb,
        ticket_id=ticket_id,
        external_auth_id=current_user.id,
        device_id=req.device_id,
        ip_address=req.ip_address,
        risk_overrides=req.risk_overrides,
        simulate_only=req.simulate_only,
    )