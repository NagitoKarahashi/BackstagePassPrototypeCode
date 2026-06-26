from datetime import date, datetime, timedelta
from fastapi import HTTPException

from app.services.profiles_service import resolve_internal_user_id

CHECKIN_REWARD_MAP = {
    1: 1,
    2: 1,
    3: 1,
    4: 3,
    5: 1,
    6: 1,
    7: 2,
}


def _resolve_internal_user_id_or_404(sb, external_auth_id: str) -> str:
    return resolve_internal_user_id(sb, external_auth_id)


def _get_profile_points(sb, internal_user_id: str) -> int:
    profile_resp = (
        sb.table("profiles")
        .select("id, fan_points")
        .eq("id", internal_user_id)
        .limit(1)
        .execute()
    )

    if not profile_resp.data:
        raise HTTPException(status_code=404, detail="Profile not found")

    return profile_resp.data[0].get("fan_points", 0) or 0


def _add_points(
    sb,
    internal_user_id: str,
    points: int,
    source: str,
    ref_type: str | None = None,
    ref_id: str | None = None,
    note: str | None = None,
):
    current_points = _get_profile_points(sb, internal_user_id)
    new_points = current_points + points

    (
        sb.table("profiles")
        .update({"fan_points": new_points})
        .eq("id", internal_user_id)
        .execute()
    )

    ledger_resp = (
        sb.table("reward_ledger")
        .insert({
            "user_id": internal_user_id,
            "source": source,
            "points": points,
            "ref_type": ref_type,
            "ref_id": ref_id,
            "note": note,
        })
        .execute()
    )

    return {
        "fan_points": new_points,
        "ledger_item": ledger_resp.data[0] if ledger_resp.data else None,
    }


def _add_points_once(
    sb,
    internal_user_id: str,
    points: int,
    source: str,
    ref_type: str | None = None,
    ref_id: str | None = None,
    note: str | None = None,
):
    query = (
        sb.table("reward_ledger")
        .select("id")
        .eq("user_id", internal_user_id)
        .eq("source", source)
    )

    if ref_type is None:
        query = query.is_("ref_type", "null")
    else:
        query = query.eq("ref_type", ref_type)

    if ref_id is None:
        query = query.is_("ref_id", "null")
    else:
        query = query.eq("ref_id", ref_id)

    existing = query.limit(1).execute()

    if existing.data:
        return {
            "fan_points": _get_profile_points(sb, internal_user_id),
            "ledger_item": None,
            "already_exists": True,
        }

    result = _add_points(
        sb=sb,
        internal_user_id=internal_user_id,
        points=points,
        source=source,
        ref_type=ref_type,
        ref_id=ref_id,
        note=note,
    )
    result["already_exists"] = False
    return result


def _deduct_points(
    sb,
    internal_user_id: str,
    points: int,
    source: str,
    ref_type: str | None = None,
    ref_id: str | None = None,
    note: str | None = None,
):
    current_points = _get_profile_points(sb, internal_user_id)

    if current_points < points:
        raise HTTPException(status_code=400, detail="Insufficient fan points")

    new_points = current_points - points

    (
        sb.table("profiles")
        .update({"fan_points": new_points})
        .eq("id", internal_user_id)
        .execute()
    )

    ledger_resp = (
        sb.table("reward_ledger")
        .insert({
            "user_id": internal_user_id,
            "source": source,
            "points": -points,
            "ref_type": ref_type,
            "ref_id": ref_id,
            "note": note,
        })
        .execute()
    )

    return {
        "fan_points": new_points,
        "ledger_item": ledger_resp.data[0] if ledger_resp.data else None,
    }


def get_reward_summary_service(sb, external_auth_id: str):
    try:
        internal_user_id = _resolve_internal_user_id_or_404(sb, external_auth_id)
        fan_points = _get_profile_points(sb, internal_user_id)
    except Exception:
        return {
            "fan_points": 0,
            "badge_count": 0,
            "ledger_count": 0,
        }

    try:
        ledger_resp = (
            sb.table("reward_ledger")
            .select("id", count="exact")
            .eq("user_id", internal_user_id)
            .execute()
        )
        ledger_count = ledger_resp.count or 0
    except Exception:
        ledger_count = 0

    try:
        badges_resp = (
            sb.table("user_badges")
            .select("id", count="exact")
            .eq("user_id", internal_user_id)
            .execute()
        )
        badge_count = badges_resp.count or 0
    except Exception:
        badge_count = 0

    return {
        "fan_points": fan_points,
        "badge_count": badge_count,
        "ledger_count": ledger_count,
    }


def get_points_ledger_service(sb, external_auth_id: str, limit: int = 50):
    internal_user_id = _resolve_internal_user_id_or_404(sb, external_auth_id)
    resp = (
        sb.table("reward_ledger")
        .select("*")
        .eq("user_id", internal_user_id)
        .order("created_at", desc=True)
        .limit(limit)
        .execute()
    )
    return {"items": resp.data or []}


def get_user_badges_service(sb, external_auth_id: str):
    internal_user_id = _resolve_internal_user_id_or_404(sb, external_auth_id)
    resp = (
        sb.table("user_badges")
        .select("*")
        .eq("user_id", internal_user_id)
        .order("awarded_at", desc=True)
        .execute()
    )
    return {"items": resp.data or []}


def get_leaderboard_service(sb, limit: int = 20):
    resp = (
        sb.table("profiles")
        .select("id, display_name, username, fan_points, avatar_url")
        .order("fan_points", desc=True)
        .limit(limit)
        .execute()
    )
    return {"items": resp.data or []}


def get_checkin_status_service(sb, external_auth_id: str):
    internal_user_id = _resolve_internal_user_id_or_404(sb, external_auth_id)
    today = date.today()

    checkins_resp = (
        sb.table("daily_checkins")
        .select("id, user_id, checkin_date, streak_day, points_awarded")
        .eq("user_id", internal_user_id)
        .order("checkin_date", desc=False)
        .limit(7)
        .execute()
    )

    checkins = checkins_resp.data or []
    checked_dates = {row["checkin_date"]: row for row in checkins}

    today_checked_in = str(today) in checked_dates
    current_streak = checkins[-1]["streak_day"] if checkins else 0

    next_streak_day = current_streak + 1
    if next_streak_day > 7:
        next_streak_day = 1

    today_reward_points = 0 if today_checked_in else CHECKIN_REWARD_MAP.get(next_streak_day, 1)

    return {
        "today_checked_in": today_checked_in,
        "current_streak": current_streak,
        "today_reward_points": today_reward_points,
        "week_progress": [],
    }


def checkin_service(sb, external_auth_id: str):
    internal_user_id = _resolve_internal_user_id_or_404(sb, external_auth_id)
    today = date.today()

    existing = (
        sb.table("daily_checkins")
        .select("id")
        .eq("user_id", internal_user_id)
        .eq("checkin_date", str(today))
        .limit(1)
        .execute()
    )

    if existing.data:
        raise HTTPException(status_code=400, detail="Already checked in today")

    latest = (
        sb.table("daily_checkins")
        .select("*")
        .eq("user_id", internal_user_id)
        .order("checkin_date", desc=True)
        .limit(1)
        .execute()
    )

    streak_day = 1
    if latest.data:
        latest_date = datetime.strptime(latest.data[0]["checkin_date"], "%Y-%m-%d").date()
        latest_streak = latest.data[0]["streak_day"] or 0

        if latest_date == today - timedelta(days=1):
            streak_day = latest_streak + 1
            if streak_day > 7:
                streak_day = 1

    points_awarded = CHECKIN_REWARD_MAP.get(streak_day, 1)

    checkin_resp = (
        sb.table("daily_checkins")
        .insert({
            "user_id": internal_user_id,
            "checkin_date": str(today),
            "streak_day": streak_day,
            "points_awarded": points_awarded,
        })
        .execute()
    )

    add_result = _add_points(
        sb=sb,
        internal_user_id=internal_user_id,
        points=points_awarded,
        source="daily_checkin",
        ref_type="daily_checkin",
        ref_id=checkin_resp.data[0]["id"] if checkin_resp.data else None,
        note=f"Day {streak_day} daily check-in",
    )

    _progress_user_missions(sb, internal_user_id=internal_user_id, category="checkin", increment=1)

    return {
        "ok": True,
        "checkin": checkin_resp.data[0] if checkin_resp.data else None,
        "fan_points": add_result["fan_points"],
        "points_awarded": points_awarded,
    }


def get_rewards_overview_service(sb, external_auth_id: str):
    internal_user_id = _resolve_internal_user_id_or_404(sb, external_auth_id)
    summary = get_reward_summary_service(sb, external_auth_id)

    try:
        checkin_status = get_checkin_status_service(sb, external_auth_id)
    except Exception as e:
        checkin_status = {
            "today_checked_in": False,
            "current_streak": 0,
            "today_reward_points": 1,
            "week_progress": [],
            "error": f"checkin status unavailable: {str(e)}",
        }

    try:
        active_missions_resp = (
            sb.table("user_missions")
            .select("id", count="exact")
            .eq("user_id", internal_user_id)
            .in_("status", ["not_started", "in_progress", "completed"])
            .execute()
        )
        active_count = active_missions_resp.count or 0
    except Exception:
        active_count = 0

    try:
        completed_unclaimed_resp = (
            sb.table("user_missions")
            .select("id", count="exact")
            .eq("user_id", internal_user_id)
            .eq("status", "completed")
            .execute()
        )
        completed_unclaimed_count = completed_unclaimed_resp.count or 0
    except Exception:
        completed_unclaimed_count = 0

    return {
        "fan_points": summary["fan_points"],
        "badge_count": summary["badge_count"],
        "ledger_count": summary["ledger_count"],
        "checkin": checkin_status,
        "missions_summary": {
            "active_count": active_count,
            "completed_unclaimed_count": completed_unclaimed_count,
        }
    }


def list_missions_service(sb, external_auth_id: str):
    internal_user_id = _resolve_internal_user_id_or_404(sb, external_auth_id)

    missions_resp = (
        sb.table("missions")
        .select("*")
        .eq("is_active", True)
        .order("sort_order", desc=False)
        .execute()
    )

    templates = missions_resp.data or []
    items = []

    for mission in templates:
        user_mission_resp = (
            sb.table("user_missions")
            .select("*")
            .eq("user_id", internal_user_id)
            .eq("mission_id", mission["id"])
            .limit(1)
            .execute()
        )

        user_mission = user_mission_resp.data[0] if user_mission_resp.data else None
        expires_at = user_mission.get("expires_at") if user_mission else None
        days_left = None

        if expires_at:
            expires_date = datetime.fromisoformat(expires_at.replace("Z", "+00:00")).date()
            days_left = max((expires_date - date.today()).days, 0)

        items.append({
            "mission_id": mission["id"],
            "code": mission["code"],
            "title": mission["title"],
            "description": mission.get("description"),
            "category": mission["category"],
            "progress": user_mission["progress"] if user_mission else 0,
            "target_value": user_mission["target_value"] if user_mission else mission["target_value"],
            "reward_points": user_mission["reward_points"] if user_mission else mission["reward_points"],
            "status": user_mission["status"] if user_mission else "not_started",
            "days_left": days_left if days_left is not None else mission.get("duration_days", 14),
        })

    return {"items": items}


def _ensure_auto_started_missions(sb, internal_user_id: str, category: str):
    missions_resp = (
        sb.table("missions")
        .select("*")
        .eq("is_active", True)
        .eq("category", category)
        .execute()
    )

    for mission in (missions_resp.data or []):
        existing = (
            sb.table("user_missions")
            .select("*")
            .eq("user_id", internal_user_id)
            .eq("mission_id", mission["id"])
            .limit(1)
            .execute()
        )

        if existing.data:
            row = existing.data[0]
            if row.get("status") == "not_started":
                now = datetime.utcnow()
                expires_at = now + timedelta(days=mission.get("duration_days", 14))
                (
                    sb.table("user_missions")
                    .update({
                        "status": "in_progress",
                        "started_at": row.get("started_at") or now.isoformat(),
                        "expires_at": row.get("expires_at") or expires_at.isoformat(),
                    })
                    .eq("id", row["id"])
                    .execute()
                )
            continue

        now = datetime.utcnow()
        expires_at = now + timedelta(days=mission.get("duration_days", 14))

        (
            sb.table("user_missions")
            .insert({
                "user_id": internal_user_id,
                "mission_id": mission["id"],
                "status": "in_progress",
                "progress": 0,
                "target_value": mission["target_value"],
                "reward_points": mission["reward_points"],
                "started_at": now.isoformat(),
                "expires_at": expires_at.isoformat(),
            })
            .execute()
        )


def start_mission_service(sb, external_auth_id: str, mission_id: str):
    internal_user_id = _resolve_internal_user_id_or_404(sb, external_auth_id)

    mission_resp = (
        sb.table("missions")
        .select("*")
        .eq("id", mission_id)
        .eq("is_active", True)
        .limit(1)
        .execute()
    )

    if not mission_resp.data:
        raise HTTPException(status_code=404, detail="Mission not found")

    mission = mission_resp.data[0]

    existing = (
        sb.table("user_missions")
        .select("*")
        .eq("user_id", internal_user_id)
        .eq("mission_id", mission_id)
        .limit(1)
        .execute()
    )

    now = datetime.utcnow()
    expires_at = now + timedelta(days=mission.get("duration_days", 14))

    if existing.data:
        row = existing.data[0]

        if row.get("status") == "not_started":
            updated = (
                sb.table("user_missions")
                .update({
                    "status": "in_progress",
                    "started_at": row.get("started_at") or now.isoformat(),
                    "expires_at": row.get("expires_at") or expires_at.isoformat(),
                })
                .eq("id", row["id"])
                .execute()
            )
            return updated.data[0] if updated.data else row

        return row

    resp = (
        sb.table("user_missions")
        .insert({
            "user_id": internal_user_id,
            "mission_id": mission_id,
            "status": "in_progress",
            "progress": 0,
            "target_value": mission["target_value"],
            "reward_points": mission["reward_points"],
            "started_at": now.isoformat(),
            "expires_at": expires_at.isoformat(),
        })
        .execute()
    )

    if not resp.data:
        raise HTTPException(status_code=400, detail="Failed to start mission")

    return resp.data[0]


def claim_mission_service(sb, external_auth_id: str, mission_id: str):
    internal_user_id = _resolve_internal_user_id_or_404(sb, external_auth_id)

    user_mission_resp = (
        sb.table("user_missions")
        .select("*")
        .eq("user_id", internal_user_id)
        .eq("mission_id", mission_id)
        .limit(1)
        .execute()
    )

    if not user_mission_resp.data:
        raise HTTPException(status_code=404, detail="User mission not found")

    user_mission = user_mission_resp.data[0]

    if user_mission["status"] != "completed":
        raise HTTPException(status_code=400, detail="Mission is not claimable")

    now = datetime.utcnow().isoformat()

    update_resp = (
        sb.table("user_missions")
        .update({
            "status": "claimed",
            "claimed_at": now,
        })
        .eq("id", user_mission["id"])
        .execute()
    )

    add_result = _add_points(
        sb=sb,
        internal_user_id=internal_user_id,
        points=user_mission["reward_points"],
        source="mission_claim",
        ref_type="mission",
        ref_id=user_mission["mission_id"],
        note="Mission reward claimed",
    )

    return {
        "ok": True,
        "mission": update_resp.data[0] if update_resp.data else None,
        "fan_points": add_result["fan_points"],
    }


def _progress_user_missions(sb, internal_user_id: str, category: str, increment: int = 1):
    _ensure_auto_started_missions(sb, internal_user_id, category)

    user_missions_resp = (
        sb.table("user_missions")
        .select("id, user_id, mission_id, status, progress, target_value, started_at, completed_at")
        .eq("user_id", internal_user_id)
        .in_("status", ["in_progress", "not_started"])
        .execute()
    )

    user_missions = user_missions_resp.data or []
    if not user_missions:
        return

    mission_ids = [row["mission_id"] for row in user_missions if row.get("mission_id")]
    if not mission_ids:
        return

    missions_resp = (
        sb.table("missions")
        .select("id, category, target_value")
        .in_("id", mission_ids)
        .eq("is_active", True)
        .execute()
    )

    mission_map = {m["id"]: m for m in (missions_resp.data or [])}

    for row in user_missions:
        mission_template = mission_map.get(row.get("mission_id"))
        if not mission_template:
            continue

        if mission_template.get("category") != category:
            continue

        current_progress = row.get("progress", 0) or 0
        new_progress = current_progress + increment
        target = row.get("target_value", 0) or mission_template.get("target_value", 0) or 0

        payload = {
            "progress": new_progress,
        }

        if row.get("status") == "not_started":
            payload["status"] = "in_progress"
            payload["started_at"] = row.get("started_at") or datetime.utcnow().isoformat()

        if target > 0 and new_progress >= target:
            payload["status"] = "completed"
            payload["completed_at"] = datetime.utcnow().isoformat()

        (
            sb.table("user_missions")
            .update(payload)
            .eq("id", row["id"])
            .execute()
        )
        

def handle_order_reward(sb, internal_user_id: str, order_id: str):
    _progress_user_missions(sb, internal_user_id=internal_user_id, category="order", increment=1)

    return _add_points_once(
        sb=sb,
        internal_user_id=internal_user_id,
        points=50,
        source="order_complete",
        ref_type="order",
        ref_id=str(order_id),
        note="Order completed reward",
    )


def handle_chat_reward(sb, internal_user_id: str, message_id: str | None = None):
    _progress_user_missions(sb, internal_user_id=internal_user_id, category="chat", increment=1)

    return {
        "ok": True,
        "message_id": message_id,
    }


def handle_event_checkin_reward(sb, internal_user_id: str, ticket_id: str):
    _progress_user_missions(sb, internal_user_id=internal_user_id, category="checkin", increment=1)

    return _add_points_once(
        sb=sb,
        internal_user_id=internal_user_id,
        points=20,
        source="event_checkin",
        ref_type="ticket",
        ref_id=str(ticket_id),
        note="Event ticket check-in reward",
    )


def list_reward_catalog_service(sb):
    resp = (
        sb.table("redeem_rewards")
        .select("*")
        .eq("is_active", True)
        .order("created_at", desc=False)
        .execute()
    )
    return {"items": resp.data or []}


def redeem_reward_service(sb, external_auth_id: str, reward_id: str):
    internal_user_id = _resolve_internal_user_id_or_404(sb, external_auth_id)

    reward_resp = (
        sb.table("redeem_rewards")
        .select("*")
        .eq("id", reward_id)
        .eq("is_active", True)
        .limit(1)
        .execute()
    )

    if not reward_resp.data:
        raise HTTPException(status_code=404, detail="Reward not found")

    reward = reward_resp.data[0]

    stock = reward.get("stock")
    if stock is not None and stock <= 0:
        raise HTTPException(status_code=400, detail="Reward out of stock")

    deduct_result = _deduct_points(
        sb=sb,
        internal_user_id=internal_user_id,
        points=reward["cost_points"],
        source="reward_redeem",
        ref_type="redeem_reward",
        ref_id=reward_id,
        note=f"Redeemed {reward['title']}",
    )

    redemption_resp = (
        sb.table("reward_redemptions")
        .insert({
            "user_id": internal_user_id,
            "reward_id": reward_id,
            "cost_points": reward["cost_points"],
            "status": "redeemed",
        })
        .execute()
    )

    if stock is not None:
        (
            sb.table("redeem_rewards")
            .update({"stock": stock - 1})
            .eq("id", reward_id)
            .execute()
        )

    return {
        "ok": True,
        "redemption": redemption_resp.data[0] if redemption_resp.data else None,
        "fan_points": deduct_result["fan_points"],
    }


def list_my_redemptions_service(sb, external_auth_id: str):
    internal_user_id = _resolve_internal_user_id_or_404(sb, external_auth_id)

    resp = (
        sb.table("reward_redemptions")
        .select("*")
        .eq("user_id", internal_user_id)
        .order("created_at", desc=True)
        .execute()
    )
    return {"items": resp.data or []}