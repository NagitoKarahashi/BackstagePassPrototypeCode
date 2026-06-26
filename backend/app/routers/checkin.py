from fastapi import APIRouter, Depends
from supabase import Client
from app.core.deps import supabase_dep
from app.schemas.checkin import CheckInRequest
from fastapi import APIRouter, Depends
from supabase import Client
from app.core.deps import supabase_dep
from app.schemas.checkin import CheckInRequest
from app.services.checkin_service import check_in_ticket_service

router = APIRouter(prefix="/checkin", tags=["checkin"])


@router.post("")
def check_in(req: CheckInRequest, sb: Client = Depends(supabase_dep)):
    return check_in_ticket_service(
        sb=sb,
        ticket_id=req.ticket_id,
        scanned_by=req.scanned_by,
        scanner_device_id=req.scanner_device_id,
        scanned_qr_token=req.scanned_qr_token,
        note=req.note,
        ip_address=req.ip_address,
        risk_overrides=req.risk_overrides,
        simulate_only=req.simulate_only,
    )