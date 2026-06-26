from pydantic import BaseModel
from typing import Optional, List


class CreateListingIn(BaseModel):
    ticket_id: str
    listing_price: float
    currency: str = "USDC"


class ListingOut(BaseModel):
    id: str
    ticket_id: str
    seller_user_id: str
    seller_wallet: Optional[str] = None
    listing_price: float
    currency: str
    status: str
    buyer_user_id: Optional[str] = None
    buyer_wallet: Optional[str] = None
    sold_at: Optional[str] = None
    cancelled_at: Optional[str] = None
    tx_hash: Optional[str] = None
    created_at: Optional[str] = None


class TicketHistoryOut(BaseModel):
    id: str
    ticket_id: str
    from_user_id: Optional[str] = None
    to_user_id: Optional[str] = None
    from_wallet: Optional[str] = None
    to_wallet: Optional[str] = None
    action: str
    tx_hash: Optional[str] = None
    note: Optional[str] = None
    created_at: Optional[str] = None