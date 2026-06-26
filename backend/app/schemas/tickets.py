from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class TicketEventBrief(BaseModel):
    id: str
    event_code: Optional[str] = None
    title: Optional[str] = None
    artist: Optional[str] = None
    genre: Optional[str] = None
    city: Optional[str] = None
    start_time: Optional[str] = None
    poster_url: Optional[str] = None


class TicketItem(BaseModel):
    id: str
    user_id: str
    order_id: Optional[str] = None
    event_id: Optional[str] = None
    event_uuid: Optional[str] = None
    token_id: Optional[str] = None
    contract_address: Optional[str] = None
    chain: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    qr_payload: Optional[str] = None
    status: str
    is_listed: bool = False
    transfer_locked: bool = False
    resale_allowed: bool = True
    last_transfer_at: Optional[str] = None
    created_at: Optional[str] = None


class TicketListResponse(BaseModel):
    items: List[TicketItem] = Field(default_factory=list)


class TicketDetailResponse(BaseModel):
    ticket: TicketItem
    event: Optional[TicketEventBrief] = None
    current_listing: Optional[Dict[str, Any]] = None
    history_preview: List[Dict[str, Any]] = Field(default_factory=list)


class TicketQrResponse(BaseModel):
    ticket_id: str
    status: str
    qr_payload: Optional[str] = None


class TicketHistoryItem(BaseModel):
    id: str
    ticket_id: str
    from_user_id: Optional[str] = None
    to_user_id: Optional[str] = None
    from_wallet_address: Optional[str] = None
    to_wallet_address: Optional[str] = None
    transfer_type: str
    transfer_status: str
    risk_level: Optional[str] = None
    risk_type: Optional[str] = None
    note: Optional[str] = None
    created_at: Optional[str] = None


class TicketHistoryResponse(BaseModel):
    items: List[TicketHistoryItem] = Field(default_factory=list)


class TransferTicketRequest(BaseModel):
    to_user_id: str
    to_wallet_address: Optional[str] = None
    note: Optional[str] = None
    device_id: Optional[str] = None
    ip_address: Optional[str] = None


class TransferTicketResponse(BaseModel):
    status: str
    message: str
    ticket_id: str
    from_user_id: str
    to_user_id: str
    risk: Dict[str, Any] = Field(default_factory=dict)


class RefundTicketRequest(BaseModel):
    device_id: Optional[str] = None
    ip_address: Optional[str] = None
    risk_overrides: Optional[Dict[str, Any]] = Field(default_factory=dict)
    simulate_only: bool = False

class RefundTicketResponse(BaseModel):
    status: str
    result: Optional[Any] = None
    message: Optional[str] = None
    risk: Dict[str, Any] = Field(default_factory=dict)


class TicketMarketStatusResponse(BaseModel):
    ticket_id: str
    is_listed: bool = False
    transfer_locked: bool = False
    resale_allowed: bool = True
    listing: Optional[Dict[str, Any]] = None


class CreateListingRequest(BaseModel):
    ticket_id: str
    listing_price: float
    currency: str = "USD"
    expires_at: Optional[str] = None


class ListingItem(BaseModel):
    id: str
    ticket_id: str
    seller_user_id: str
    buyer_user_id: Optional[str] = None
    listing_price: float
    currency: str = "USD"
    status: str
    expires_at: Optional[str] = None
    sold_at: Optional[str] = None
    created_at: Optional[str] = None


class ListingListResponse(BaseModel):
    items: List[ListingItem] = Field(default_factory=list)