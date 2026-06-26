from fastapi import APIRouter, HTTPException
from app.services.ticket_service import (
    list_my_tickets,
    get_ticket_detail,
    check_in_ticket,
)

router = APIRouter()

@router.get("/me/tickets")
def get_my_tickets(user_id: str):
    return list_my_tickets(user_id)

@router.get("/tickets/{ticket_id}")
def get_ticket(ticket_id: str):
    ticket = get_ticket_detail(ticket_id)
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    return ticket

@router.post("/tickets/{ticket_id}/check-in")
def check_in(ticket_id: str):
    result = check_in_ticket(ticket_id)
    if not result["ok"]:
        raise HTTPException(status_code=400, detail=result["message"])
    return result