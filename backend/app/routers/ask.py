from fastapi import APIRouter
from app.schemas.ask import AskRequest
from app.services.ask_service import answer_question

router = APIRouter(prefix="/ask", tags=["ask"])


@router.post("")
def ask(req: AskRequest):
    return answer_question(req)