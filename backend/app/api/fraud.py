from fastapi import APIRouter
from app.schemas.fraud import OrderInfo
from app.services.fraud_service import evaluate_fraud

router = APIRouter()

@router.post("/fraud/check_order")
def fraud_check(order: OrderInfo):
    return {"order": order.dict(), "evaluation": evaluate_fraud(order)}
