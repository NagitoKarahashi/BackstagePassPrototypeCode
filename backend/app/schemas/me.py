from typing import Any, List, Optional
from pydantic import BaseModel


class MeOverviewOut(BaseModel):
    profile: dict
    stats: dict
    recent_orders: List[dict]
    recent_tickets: List[dict]
    badges: List[dict]


class MeHistoryOut(BaseModel):
    orders: List[dict]
    tickets: List[dict]