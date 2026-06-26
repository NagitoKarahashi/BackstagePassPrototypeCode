from typing import Any, Dict, List, Optional
from pydantic import BaseModel


class FraudCheckRequest(BaseModel):
    order_id: Optional[str] = None
    user_id: Optional[str] = None
    event_uuid: Optional[str] = None
    qty: Optional[int] = None
    total_amount: Optional[float] = None
    device_id: Optional[str] = None
    ip_address: Optional[str] = None

    # optional externally supplied signals from frontend / other services
    recent_order_count: Optional[int] = None
    same_event_order_count: Optional[int] = None
    refund_ratio: Optional[float] = None
    transfer_attempts_recent: Optional[int] = None
    qr_duplicate_attempts_recent: Optional[int] = None
    invalid_checkin_count_recent: Optional[int] = None
    chat_spam_count_recent: Optional[int] = None
    blocked_action_retry_count: Optional[int] = None
    post_refund_chat_attempt: Optional[bool] = None

    location_mismatch: Optional[bool] = None
    device_multi_account_count: Optional[int] = None
    high_velocity_order: Optional[bool] = None
    wallet_reuse: Optional[bool] = None

    # temporal decay support
    last_risk_at: Optional[str] = None
    risk_updated_at: Optional[str] = None
    latest_signal_at: Optional[str] = None
    latest_abnormal_at: Optional[str] = None

    extra_context: Optional[Dict[str, Any]] = None


class FraudResult(BaseModel):
    order_id: Optional[str] = None
    user_id: Optional[str] = None

    risk_score: float
    raw_risk_score: Optional[float] = None
    risk_level: str
    risk_type: str
    reasons: List[str]
    signals: Dict[str, Any]
    recommended_action: str

    last_risk_at: Optional[str] = None
    decay_applied: Optional[bool] = None
    decay_factor: Optional[float] = None
    days_since_risk: Optional[float] = None


class FraudDetailResponse(BaseModel):
    order: Optional[Dict[str, Any]] = None
    fraud: FraudResult