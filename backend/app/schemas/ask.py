from pydantic import BaseModel
from typing import Any, Dict, List, Optional


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