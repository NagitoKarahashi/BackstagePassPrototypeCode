from fastapi import APIRouter, HTTPException
from app.services.ticket_service import check_in_ticket

router = APIRouter()

@router.post("/checkin/verify/{ticket_id}")
def verify_checkin(ticket_id: str):
    result = check_in_ticket(ticket_id)
    if not result["ok"]:
        raise HTTPException(status_code=400, detail=result["message"])
    return result