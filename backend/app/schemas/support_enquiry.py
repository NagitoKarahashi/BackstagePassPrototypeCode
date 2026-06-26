from datetime import datetime
from typing import List, Literal, Optional
from uuid import UUID

from pydantic import BaseModel, Field


SupportCategory = Literal[
    "general",
    "refund",
    "transfer",
    "ticket",
    "event",
    "risk",
    "account",
    "technical",
]

SupportStatus = Literal[
    "open",
    "in_review",
    "resolved",
    "closed",
]

SupportSource = Literal[
    "manual",
    "chatbot",
    "refund_flow",
    "transfer_flow",
    "risk_flow",
]


class SupportEnquiryCreate(BaseModel):
    category: SupportCategory
    subject: str = Field(min_length=1, max_length=200)
    message: str = Field(min_length=1, max_length=4000)
    order_id: Optional[UUID] = None
    event_uuid: Optional[UUID] = None
    ticket_id: Optional[UUID] = None
    source: SupportSource = "manual"


class SupportEnquiryOut(BaseModel):
    id: UUID
    user_id: UUID
    category: SupportCategory
    subject: str
    message: str
    order_id: Optional[UUID] = None
    event_uuid: Optional[UUID] = None
    ticket_id: Optional[UUID] = None
    status: SupportStatus
    source: SupportSource
    created_at: datetime
    updated_at: datetime


class SupportEnquiryListResponse(BaseModel):
    items: List[SupportEnquiryOut]
    total: int