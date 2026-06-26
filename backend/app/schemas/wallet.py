from typing import Any, Dict, Optional
from pydantic import BaseModel


class WalletMeOut(BaseModel):
    wallet_address: Optional[str] = None
    total_tickets: int
    minted_tickets: int
    listed_tickets: int


class WalletTicketOut(BaseModel):
    id: str
    order_id: Optional[str] = None
    event_id: Optional[str] = None
    event_uuid: Optional[str] = None
    title: Optional[str] = None
    artist: Optional[str] = None
    city: Optional[str] = None
    genre: Optional[str] = None
    start_time: Optional[str] = None
    poster_url: Optional[str] = None
    status: str
    token_id: Optional[str] = None
    contract_address: Optional[str] = None
    chain: Optional[str] = None
    owner_wallet: Optional[str] = None
    mint_status: str
    minted_at: Optional[str] = None
    tx_hash: Optional[str] = None
    metadata_uri: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    is_listed: bool = False
    created_at: Optional[str] = None