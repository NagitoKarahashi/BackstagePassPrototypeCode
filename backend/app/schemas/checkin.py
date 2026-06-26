from pydantic import BaseModel
from typing import Optional, Dict, Any


class CheckInRequest(BaseModel):
    ticket_id: str
    scanned_by: Optional[str] = None
    scanner_device_id: Optional[str] = None
    scanned_qr_token: Optional[str] = None
    note: Optional[str] = None
    ip_address: Optional[str] = None
    risk_overrides: Optional[Dict[str, Any]] = None
    simulate_only: bool = False