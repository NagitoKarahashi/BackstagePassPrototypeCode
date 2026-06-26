from fastapi import APIRouter, Depends, Query
from supabase import Client

from app.core.deps import supabase_dep, current_user_dep
from app.services.rewards_service import (
    get_rewards_overview_service,
    get_checkin_status_service,
    checkin_service,
    list_missions_service,
    start_mission_service,
    claim_mission_service,
    list_reward_catalog_service,
    redeem_reward_service,
    list_my_redemptions_service,
    get_reward_summary_service,
    get_points_ledger_service,
    get_user_badges_service,
    get_leaderboard_service,
)

router = APIRouter(prefix="/rewards", tags=["rewards"])


@router.get("/overview")
def rewards_overview(
    current_user=Depends(current_user_dep),
    sb: Client = Depends(supabase_dep),
):
    return get_rewards_overview_service(sb, current_user.id)


@router.get("/checkin-status")
def checkin_status(
    current_user=Depends(current_user_dep),
    sb: Client = Depends(supabase_dep),
):
    return get_checkin_status_service(sb, current_user.id)


@router.post("/checkin")
def checkin(
    current_user=Depends(current_user_dep),
    sb: Client = Depends(supabase_dep),
):
    return checkin_service(sb, current_user.id)


@router.get("/missions")
def missions(
    current_user=Depends(current_user_dep),
    sb: Client = Depends(supabase_dep),
):
    return list_missions_service(sb, current_user.id)


@router.post("/missions/{mission_id}/start")
def start_mission(
    mission_id: str,
    current_user=Depends(current_user_dep),
    sb: Client = Depends(supabase_dep),
):
    return start_mission_service(sb, current_user.id, mission_id)


@router.post("/missions/{mission_id}/claim")
def claim_mission(
    mission_id: str,
    current_user=Depends(current_user_dep),
    sb: Client = Depends(supabase_dep),
):
    return claim_mission_service(sb, current_user.id, mission_id)


@router.get("/catalog")
def reward_catalog(
    sb: Client = Depends(supabase_dep),
):
    return list_reward_catalog_service(sb)


@router.post("/redeem/{reward_id}")
def redeem_reward(
    reward_id: str,
    current_user=Depends(current_user_dep),
    sb: Client = Depends(supabase_dep),
):
    return redeem_reward_service(sb, current_user.id, reward_id)


@router.get("/my-redemptions")
def my_redemptions(
    current_user=Depends(current_user_dep),
    sb: Client = Depends(supabase_dep),
):
    return list_my_redemptions_service(sb, current_user.id)


@router.get("/summary")
def reward_summary(
    current_user=Depends(current_user_dep),
    sb: Client = Depends(supabase_dep),
):
    return get_reward_summary_service(sb, current_user.id)


@router.get("/ledger")
def points_ledger(
    current_user=Depends(current_user_dep),
    limit: int = Query(default=50, ge=1, le=200),
    sb: Client = Depends(supabase_dep),
):
    return get_points_ledger_service(sb, current_user.id, limit)


@router.get("/badges")
def badges(
    current_user=Depends(current_user_dep),
    sb: Client = Depends(supabase_dep),
):
    return get_user_badges_service(sb, current_user.id)


@router.get("/leaderboard")
def leaderboard(
    limit: int = Query(default=20, ge=1, le=100),
    sb: Client = Depends(supabase_dep),
):
    return get_leaderboard_service(sb, limit)