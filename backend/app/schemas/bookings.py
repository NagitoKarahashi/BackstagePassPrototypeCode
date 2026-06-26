from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class BookingCreateRequest(BaseModel):
    event_id: str
    quantity: int = Field(ge=1, le=10)
    unit_price: Optional[float] = None
    currency: str = "JPY"
    payment_method: Optional[str] = None
    payment_ref: Optional[str] = None
    wallet_address: Optional[str] = None
    device_id: Optional[str] = None
    ip_address: Optional[str] = None


class BookingConfirmRequest(BaseModel):
    payment_ref: Optional[str] = None
    paid_amount: Optional[float] = None


class BookingCancelRequest(BaseModel):
    reason: Optional[str] = None


class BookingOut(BaseModel):
    id: str
    user_id: str
    event_id: str
    quantity: int
    status: str
    total_amount: Optional[float] = None
    currency: Optional[str] = None
    payment_ref: Optional[str] = None
    created_at: Optional[datetime] = None