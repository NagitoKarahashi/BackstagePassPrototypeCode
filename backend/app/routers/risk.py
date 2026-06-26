from fastapi import APIRouter, Depends, Query
from supabase import Client

from app.core.deps import supabase_dep, get_current_user
from app.schemas.risk import RiskEvaluateRequest
from app.services.risk_access_service import (
    evaluate_risk_summary_service,
    get_user_risk_summary_service,
)

router = APIRouter(prefix="/risk", tags=["risk"])


@router.get("/me")
def get_my_risk_summary(
    lang: str = Query(default="en"),
    sb: Client = Depends(supabase_dep),
    current_user=Depends(get_current_user),
):
    user_id = str(current_user.id)
    return get_user_risk_summary_service(sb, user_id, lang=lang)


@router.post("/evaluate")
def evaluate_risk_summary(
    req: RiskEvaluateRequest,
    lang: str = Query(default="en"),
    sb: Client = Depends(supabase_dep),
):
    return evaluate_risk_summary_service(sb, req.model_dump(), lang=lang)