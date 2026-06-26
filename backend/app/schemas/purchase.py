from typing import Optional
from pydantic import BaseModel, Field


class PurchaseRequest(BaseModel):
    event_id: str
    ticket_tier_id: str
    quantity: int = Field(gt=0)
    wallet_address: Optional[str] = None
    device_id: Optional[str] = None
    ip_address: Optional[str] = None


class PurchaseResponse(BaseModel):
    order_id: str
    status: str
    message: str


class ConfirmPurchaseRequest(BaseModel):
    payment_ref: str


class ConfirmPurchaseResponse(BaseModel):
    order_id: str
    order_status: str
    tickets_issued: int