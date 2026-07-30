from fastapi import APIRouter, Depends
from supabase import Client

from app.core.deps import current_user_dep, supabase_dep
from app.schemas.ask import AskRequest, ChatbotPurchaseConfirmRequest
from app.services.chatbot_events_service import confirm_chatbot_purchase
from app.services.ask_service import answer_question

router = APIRouter(prefix="/ask", tags=["ask"])


@router.post("")
def ask(
    req: AskRequest,
    sb: Client = Depends(supabase_dep),
):
    return answer_question(req, sb)


@router.post("/purchase/confirm")
def confirm_purchase(
    req: ChatbotPurchaseConfirmRequest,
    current_user=Depends(current_user_dep),
    sb: Client = Depends(supabase_dep),
):
    return confirm_chatbot_purchase(
        sb=sb,
        external_auth_id=current_user.id,
        event_id=req.event_id,
        quantity=req.quantity,
        lang=req.lang,
    )
