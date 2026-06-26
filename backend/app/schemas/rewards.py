from typing import Optional
from pydantic import BaseModel


class RewardSummaryOut(BaseModel):
    fan_points: int
    badge_count: int
    ledger_count: int


class RewardLedgerItemOut(BaseModel):
    id: str
    user_id: str
    source: str
    points: int
    ref_type: Optional[str] = None
    ref_id: Optional[str] = None
    note: Optional[str] = None
    created_at: Optional[str] = None


class UserBadgeOut(BaseModel):
    id: str
    user_id: str
    badge_code: str
    badge_name: str
    badge_desc: Optional[str] = None
    icon_url: Optional[str] = None
    awarded_at: Optional[str] = None


class CheckinStatusOut(BaseModel):
    today_checked_in: bool
    current_streak: int
    today_reward_points: int
    week_progress: list[dict]


class MissionOut(BaseModel):
    mission_id: str
    code: str
    title: str
    description: Optional[str] = None
    category: str
    progress: int
    target_value: int
    reward_points: int
    status: str
    days_left: Optional[int] = None


class RewardCatalogItemOut(BaseModel):
    id: str
    code: str
    title: str
    description: Optional[str] = None
    cost_points: int
    stock: Optional[int] = None
    reward_type: str
    image_url: Optional[str] = None


class RedemptionOut(BaseModel):
    id: str
    reward_id: str
    cost_points: int
    status: str
    created_at: Optional[str] = None