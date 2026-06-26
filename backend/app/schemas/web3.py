from pydantic import BaseModel
from typing import Optional


class MintTicketOut(BaseModel):
    ticket_id: str
    mint_status: str
    token_id: Optional[str] = None
    contract_address: Optional[str] = None
    chain: Optional[str] = None
    owner_wallet: Optional[str] = None
    tx_hash: Optional[str] = None
    minted_at: Optional[str] = None