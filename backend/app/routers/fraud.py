from fastapi import APIRouter, Depends
from supabase import Client

from app.core.deps import supabase_dep
from app.schemas.fraud import FraudCheckRequest
from app.services.fraud_service import (
    check_order_fraud_service,
    get_order_fraud_detail_service,
    evaluate_fraud_service,
)

router = APIRouter(prefix="/fraud", tags=["fraud"])


@router.post("/check-order")
def check_order(req: FraudCheckRequest, sb: Client = Depends(supabase_dep)):
    if not req.order_id:
        return {"detail": "order_id is required for /check-order"}
    return check_order_fraud_service(sb, req.order_id)


@router.post("/evaluate")
def evaluate_risk(req: FraudCheckRequest, sb: Client = Depends(supabase_dep)):
    return evaluate_fraud_service(sb, req.model_dump())


@router.get("/orders/{order_id}")
def get_order_fraud_detail(order_id: str, sb: Client = Depends(supabase_dep)):
    return get_order_fraud_detail_service(sb, order_id)