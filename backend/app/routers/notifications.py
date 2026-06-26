from fastapi import APIRouter, Depends, Query
from supabase import Client

from app.core.deps import supabase_dep, get_current_user
from app.services.notifications_service import get_my_notifications_service

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.get("/my")
def get_my_notifications(
    limit: int = Query(default=20, ge=1, le=100),
    sb: Client = Depends(supabase_dep),
    current_user=Depends(get_current_user),
):
    return get_my_notifications_service(sb, str(current_user.id), limit)