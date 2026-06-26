from fastapi import APIRouter
from app.services.profile_service import get_my_profile, update_my_profile

router = APIRouter()

@router.get("/me/profile")
def get_profile(user_id: str):
    return get_my_profile(user_id)

@router.patch("/me/profile")
def patch_profile(user_id: str, payload: dict):
    return update_my_profile(user_id, payload)