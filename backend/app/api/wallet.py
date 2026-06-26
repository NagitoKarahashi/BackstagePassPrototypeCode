from fastapi import APIRouter
from app.services.events_service import get_events_df

router = APIRouter()

@router.get("/wallet/{address}/tickets")
def get_wallet_tickets(address: str):
    events_df = get_events_df()
    if events_df.empty:
        return {"address": address, "tickets": []}
    sample_events = events_df.sample(n=min(3, len(events_df)), random_state=42)
    tickets = []
    for _, row in sample_events.iterrows():
        tickets.append({
            "nft_id": f"nft_{row['event_id']}",
            "event_id": row["event_id"],
            "title": row["title"],
            "artist": row["artist"],
            "genre": row["genre"],
            "city": row["city"],
            "start_time": row["start_time"],
            "desc": row["desc"],
            "chain": "Polygon (testnet)",
            "contract_address": "0xDEADBEEFDEADBEEFDEADBEEFDEADBEEFDEAD0001",
            "token_standard": "ERC-721",
            "status": "valid",
        })
    return {"address": address, "tickets": tickets}
