from pydantic import BaseModel, Field
from typing import Any, Dict, List, Literal, Optional


class AskRequest(BaseModel):
    question: str
    context: Optional[Dict[str, Any]] = None


class AskResponse(BaseModel):
    answer: str
    citations: List[str]
    scores: List[float]
    intent: str
    lang: str
    risk_level: Optional[str] = None
    risk_score: Optional[float] = None
    risk_type: Optional[str] = None
    risk_reasons: List[str] = Field(default_factory=list)
    recommended_action: Optional[str] = None
    answer_mode: Optional[str] = None
    next_actions: List[str] = Field(default_factory=list)
    events: List[Dict[str, Any]] = Field(default_factory=list)
    event: Optional[Dict[str, Any]] = None
    action: Optional[Dict[str, Any]] = None
    order: Optional[Dict[str, Any]] = None
    payment: Optional[Any] = None


class ChatbotPurchaseConfirmRequest(BaseModel):
    event_id: str
    quantity: int = Field(default=1, ge=1, le=6)
    lang: Literal["en", "zh"] = "en"
