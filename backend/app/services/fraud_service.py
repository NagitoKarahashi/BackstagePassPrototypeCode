import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

from fastapi import HTTPException


BASE_DIR = Path(__file__).resolve().parent.parent
RISK_RULES_PATH = BASE_DIR / "config" / "risk_rules.json"

ORDER_SELECT = """
id,
user_id,
event_id,
event_uuid,
qty,
total_amount,
status,
created_at
"""


def _bool(v: Any) -> bool:
    return bool(v)


def _int(v: Any) -> int:
    try:
        return int(v or 0)
    except Exception:
        return 0


def _float(v: Any) -> float:
    try:
        return float(v or 0.0)
    except Exception:
        return 0.0


def _cap(score: float) -> float:
    return round(min(max(score, 0.0), 1.0), 4)


def _load_risk_rules() -> Dict[str, Any]:
    if not RISK_RULES_PATH.exists():
        return {
            "weights": {
                "high_velocity_order": 0.30,
                "device_multi_account": 0.25,
                "wallet_reuse": 0.20,
                "location_mismatch": 0.10,
                "high_order_amount": 0.15,
                "qr_duplicate_attempt": 0.40,
                "large_qty": 0.20,
                "multiple_recent_orders": 0.20,
                "repeat_orders_same_event": 0.15,
                "high_refund_ratio": 0.20,
                "high_transfer_attempts": 0.20,
            },
            "thresholds": {
                "approve_max": 0.39,
                "review_max": 0.74,
            },
        }
    with open(RISK_RULES_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


RISK_RULES = _load_risk_rules()
WEIGHTS = RISK_RULES.get("weights", {})
THRESHOLDS = RISK_RULES.get("thresholds", {})


def _safe_count(query) -> int:
    try:
        res = query.execute()
        return int(res.count or 0)
    except Exception:
        return 0


def _safe_fetch_one(query) -> Optional[Dict[str, Any]]:
    try:
        res = query.limit(1).execute()
        if res.data:
            return res.data[0]
        return None
    except Exception:
        return None


def _score_to_level(score: float) -> str:
    approve_max = float(THRESHOLDS.get("approve_max", 0.39))
    review_max = float(THRESHOLDS.get("review_max", 0.74))
    if score <= approve_max:
        return "low"
    if score <= review_max:
        return "medium"
    return "high"


def _recommended_action(level: str, risk_type: str) -> str:
    if level == "high":
        if risk_type == "account_takeover":
            return "freeze_sensitive_actions"
        return "manual_review"
    if level == "medium":
        return "additional_verification"
    return "allow"


def _normalize_signal_bool(v: Any) -> bool:
    return bool(v) is True


def _parse_dt(value: Any) -> Optional[datetime]:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
    if not isinstance(value, str):
        return None

    text = value.strip()
    if not text:
        return None

    try:
        if text.endswith("Z"):
            text = text[:-1] + "+00:00"
        dt = datetime.fromisoformat(text)
        return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
    except Exception:
        return None


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


def _days_since(ts: Optional[datetime], now: Optional[datetime] = None) -> float:
    if ts is None:
        return 0.0
    now = now or _now_utc()
    delta = now - ts
    return max(delta.total_seconds() / 86400.0, 0.0)


def _is_severe_risk_type(risk_type: str) -> bool:
    return risk_type in {"account_takeover", "scalping", "abuse"}


def _get_decay_factor(days_since: float, severe: bool = False) -> float:
    # severe 风险衰减更慢
    if severe:
        if days_since <= 3:
            return 1.0
        if days_since <= 7:
            return 0.9
        if days_since <= 14:
            return 0.7
        if days_since <= 30:
            return 0.4
        if days_since <= 60:
            return 0.2
        return 0.0

    if days_since <= 1:
        return 1.0
    if days_since <= 3:
        return 0.8
    if days_since <= 7:
        return 0.6
    if days_since <= 14:
        return 0.35
    if days_since <= 30:
        return 0.15
    return 0.0


def _apply_score_decay(
    raw_score: float,
    reference_ts: Optional[datetime],
    severe: bool = False,
    now: Optional[datetime] = None,
) -> Dict[str, Any]:
    raw_score = _cap(raw_score)
    if raw_score <= 0.0 or reference_ts is None:
        return {
            "raw_risk_score": raw_score,
            "risk_score": raw_score,
            "decay_applied": False,
            "decay_factor": 1.0,
            "days_since_risk": 0.0,
        }

    days = _days_since(reference_ts, now=now)
    factor = _get_decay_factor(days, severe=severe)
    decayed = _cap(raw_score * factor)

    return {
        "raw_risk_score": raw_score,
        "risk_score": decayed,
        "decay_applied": factor < 1.0,
        "decay_factor": round(factor, 4),
        "days_since_risk": round(days, 4),
    }


def _extract_reference_risk_time(payload: Dict[str, Any], order: Optional[Dict[str, Any]] = None) -> Optional[datetime]:
    # 优先使用显式传入的风险时间
    for key in ["last_risk_at", "risk_updated_at", "latest_signal_at", "latest_abnormal_at"]:
        dt = _parse_dt(payload.get(key))
        if dt is not None:
            return dt

    # 没有的话，退回到订单创建时间，至少让旧订单风险自然回落
    if order:
        dt = _parse_dt(order.get("created_at"))
        if dt is not None:
            return dt

    return None


def _build_base_context_from_order(sb, order_id: str) -> Dict[str, Any]:
    order = _safe_fetch_one(
        sb.table("orders")
        .select(ORDER_SELECT)
        .eq("id", order_id)
    )
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    return {
        "order": order,
        "order_id": order.get("id"),
        "user_id": order.get("user_id"),
        "event_uuid": order.get("event_uuid"),
        "qty": order.get("qty") or 0,
        "total_amount": float(order.get("total_amount") or 0),
    }


def _collect_db_signals(sb, ctx: Dict[str, Any]) -> Dict[str, Any]:
    user_id = ctx.get("user_id")
    event_uuid = ctx.get("event_uuid")
    qty = int(ctx.get("qty") or 0)
    total_amount = float(ctx.get("total_amount") or 0)

    signals: Dict[str, Any] = {
        "large_qty": qty >= 5,
        "high_order_amount": total_amount >= 1000,
        "multiple_recent_orders": False,
        "repeat_orders_same_event": False,
        "recent_order_count": 0,
        "same_event_order_count": 0,
        "refund_ratio": 0.0,
        "high_refund_ratio": False,
        "transfer_attempts_recent": 0,
        "high_transfer_attempts": False,
        "qr_duplicate_attempt": False,
        "qr_duplicate_attempts_recent": 0,
        "invalid_checkin_count_recent": 0,
        "chat_spam_count_recent": 0,
        "blocked_action_retry_count": 0,
        "post_refund_chat_attempt": False,
        "device_multi_account_count": 0,
        "device_multi_account": False,
        "location_mismatch": False,
        "high_velocity_order": False,
        "wallet_reuse": False,
    }

    if user_id:
        total_order_count = _safe_count(
            sb.table("orders")
            .select("id", count="exact")
            .eq("user_id", user_id)
        )
        signals["recent_order_count"] = total_order_count
        signals["multiple_recent_orders"] = total_order_count >= 3

        refunded_order_count = _safe_count(
            sb.table("orders")
            .select("id", count="exact")
            .eq("user_id", user_id)
            .eq("status", "refunded")
        )
        refund_ratio = (refunded_order_count / total_order_count) if total_order_count > 0 else 0.0
        signals["refund_ratio"] = round(refund_ratio, 4)
        signals["high_refund_ratio"] = refund_ratio >= 0.5

    if user_id and event_uuid:
        same_event_count = _safe_count(
            sb.table("orders")
            .select("id", count="exact")
            .eq("user_id", user_id)
            .eq("event_uuid", event_uuid)
        )
        signals["same_event_order_count"] = same_event_count
        signals["repeat_orders_same_event"] = same_event_count >= 2

    if user_id:
        ticket_ids_res = (
            sb.table("tickets")
            .select("id")
            .eq("user_id", user_id)
            .execute()
        )
        ticket_ids = [t["id"] for t in (ticket_ids_res.data or []) if t.get("id")]

        if ticket_ids:
            dup_count = _safe_count(
                sb.table("check_in_logs")
                .select("id", count="exact")
                .in_("ticket_id", ticket_ids)
                .eq("result", "duplicate")
            )
            invalid_count = _safe_count(
                sb.table("check_in_logs")
                .select("id", count="exact")
                .in_("ticket_id", ticket_ids)
                .eq("result", "invalid")
            )
            blocked_count = _safe_count(
                sb.table("check_in_logs")
                .select("id", count="exact")
                .in_("ticket_id", ticket_ids)
                .eq("result", "blocked")
            )

            signals["qr_duplicate_attempts_recent"] = dup_count
            signals["qr_duplicate_attempt"] = dup_count >= 2
            signals["invalid_checkin_count_recent"] = invalid_count
            signals["blocked_action_retry_count"] = blocked_count

        chat_count = _safe_count(
            sb.table("chat_messages")
            .select("id", count="exact")
            .eq("user_id", user_id)
        )
        signals["chat_spam_count_recent"] = chat_count

        refunded_orders_resp = (
            sb.table("orders")
            .select("event_uuid")
            .eq("user_id", user_id)
            .eq("status", "refunded")
            .execute()
        )
        refunded_event_ids = [
            x.get("event_uuid") for x in (refunded_orders_resp.data or []) if x.get("event_uuid")
        ]

        if refunded_event_ids:
            rooms_resp = (
                sb.table("chat_rooms")
                .select("id")
                .eq("room_type", "event")
                .in_("event_id", refunded_event_ids)
                .execute()
            )
            refunded_room_ids = [r["id"] for r in (rooms_resp.data or []) if r.get("id")]

            if refunded_room_ids:
                post_refund_chat_count = _safe_count(
                    sb.table("chat_messages")
                    .select("id", count="exact")
                    .eq("user_id", user_id)
                    .in_("room_id", refunded_room_ids)
                )
                signals["post_refund_chat_attempt"] = post_refund_chat_count > 0

    return signals


def _merge_external_signals(signals: Dict[str, Any], payload: Dict[str, Any]) -> Dict[str, Any]:
    merged = dict(signals)

    if payload.get("recent_order_count") is not None:
        merged["recent_order_count"] = int(payload["recent_order_count"])
        merged["multiple_recent_orders"] = int(payload["recent_order_count"]) >= 3

    if payload.get("same_event_order_count") is not None:
        merged["same_event_order_count"] = int(payload["same_event_order_count"])
        merged["repeat_orders_same_event"] = int(payload["same_event_order_count"]) >= 2

    if payload.get("refund_ratio") is not None:
        merged["refund_ratio"] = float(payload["refund_ratio"])
        merged["high_refund_ratio"] = float(payload["refund_ratio"]) >= 0.5

    if payload.get("transfer_attempts_recent") is not None:
        transfer_attempts = int(payload.get("transfer_attempts_recent") or 0)
        merged["transfer_attempts_recent"] = transfer_attempts
        merged["high_transfer_attempts"] = transfer_attempts >= 3

    if payload.get("qr_duplicate_attempts_recent") is not None:
        qr_dup = int(payload.get("qr_duplicate_attempts_recent") or 0)
        merged["qr_duplicate_attempts_recent"] = qr_dup
        merged["qr_duplicate_attempt"] = qr_dup >= 2

    if payload.get("invalid_checkin_count_recent") is not None:
        merged["invalid_checkin_count_recent"] = int(payload.get("invalid_checkin_count_recent") or 0)

    if payload.get("chat_spam_count_recent") is not None:
        merged["chat_spam_count_recent"] = int(payload.get("chat_spam_count_recent") or 0)

    if payload.get("blocked_action_retry_count") is not None:
        merged["blocked_action_retry_count"] = int(payload.get("blocked_action_retry_count") or 0)

    if payload.get("post_refund_chat_attempt") is not None:
        merged["post_refund_chat_attempt"] = _normalize_signal_bool(payload.get("post_refund_chat_attempt"))

    if payload.get("device_multi_account_count") is not None:
        device_multi = int(payload.get("device_multi_account_count") or 0)
        merged["device_multi_account_count"] = device_multi
        merged["device_multi_account"] = device_multi >= 2

    if payload.get("location_mismatch") is not None:
        merged["location_mismatch"] = _normalize_signal_bool(payload.get("location_mismatch"))

    if payload.get("high_velocity_order") is not None:
        merged["high_velocity_order"] = _normalize_signal_bool(payload.get("high_velocity_order"))

    if payload.get("wallet_reuse") is not None:
        merged["wallet_reuse"] = _normalize_signal_bool(payload.get("wallet_reuse"))

    return merged


def _score_account_takeover(signals: Dict[str, Any]) -> Dict[str, Any]:
    score = 0.0
    reasons = []

    device_multi_account_count = _int(signals.get("device_multi_account_count"))
    location_mismatch = _bool(signals.get("location_mismatch"))
    wallet_reuse = _bool(signals.get("wallet_reuse"))
    transfer_attempts_recent = _int(signals.get("transfer_attempts_recent"))
    refund_ratio = _float(signals.get("refund_ratio"))
    high_velocity_order = _bool(signals.get("high_velocity_order"))

    if device_multi_account_count >= 5:
        score += 0.45
        reasons.append("device_multi_account_extreme")
    elif device_multi_account_count >= 3:
        score += 0.30
        reasons.append("device_multi_account_high")
    elif device_multi_account_count >= 2:
        score += 0.18
        reasons.append("device_multi_account_moderate")

    if location_mismatch:
        score += 0.30
        reasons.append("location_mismatch")

    if wallet_reuse:
        score += 0.25
        reasons.append("wallet_reuse")

    if transfer_attempts_recent >= 3:
        score += 0.18
        reasons.append("suspicious_transfer_pattern")
    elif transfer_attempts_recent >= 1:
        score += 0.08
        reasons.append("transfer_attempt_after_risk_signal")

    if refund_ratio >= 0.6:
        score += 0.10
        reasons.append("high_refund_ratio")
    elif refund_ratio >= 0.4:
        score += 0.05
        reasons.append("moderate_refund_ratio")

    if high_velocity_order and (location_mismatch or wallet_reuse):
        score += 0.10
        reasons.append("high_velocity_in_suspicious_context")

    if location_mismatch and wallet_reuse:
        score += 0.20
        reasons.append("high_risk_combo_location_wallet")

    if location_mismatch and device_multi_account_count >= 3:
        score += 0.20
        reasons.append("high_risk_combo_location_device")

    if wallet_reuse and transfer_attempts_recent >= 3:
        score += 0.15
        reasons.append("high_risk_combo_wallet_transfer")

    if location_mismatch and transfer_attempts_recent >= 3:
        score += 0.12
        reasons.append("high_risk_combo_location_transfer")

    force_high = False
    if location_mismatch and wallet_reuse and device_multi_account_count >= 3:
        force_high = True
        reasons.append("force_high_account_takeover_pattern")

    final_score = _cap(score)
    if force_high and final_score < 0.85:
        final_score = 0.85

    return {
        "risk_type": "account_takeover",
        "score": final_score,
        "reasons": reasons,
    }


def _score_scalping(signals: Dict[str, Any]) -> Dict[str, Any]:
    score = 0.0
    reasons = []

    high_velocity_order = _bool(signals.get("high_velocity_order"))
    large_qty = _bool(signals.get("large_qty"))
    high_order_amount = _bool(signals.get("high_order_amount"))
    recent_order_count = _int(signals.get("recent_order_count"))
    same_event_order_count = _int(signals.get("same_event_order_count"))
    refund_ratio = _float(signals.get("refund_ratio"))
    transfer_attempts_recent = _int(signals.get("transfer_attempts_recent"))
    device_multi_account_count = _int(signals.get("device_multi_account_count"))

    if high_velocity_order:
        score += 0.30
        reasons.append("high_velocity_order")

    if large_qty:
        score += 0.20
        reasons.append("large_qty")

    if high_order_amount:
        score += 0.15
        reasons.append("high_order_amount")

    if recent_order_count >= 8:
        score += 0.35
        reasons.append("multiple_recent_orders_extreme")
    elif recent_order_count >= 5:
        score += 0.25
        reasons.append("multiple_recent_orders_high")
    elif recent_order_count >= 3:
        score += 0.15
        reasons.append("multiple_recent_orders")

    if same_event_order_count >= 5:
        score += 0.25
        reasons.append("repeat_orders_same_event_extreme")
    elif same_event_order_count >= 3:
        score += 0.18
        reasons.append("repeat_orders_same_event_high")
    elif same_event_order_count >= 2:
        score += 0.10
        reasons.append("repeat_orders_same_event")

    if refund_ratio >= 0.8:
        score += 0.22
        reasons.append("high_refund_ratio_extreme")
    elif refund_ratio >= 0.6:
        score += 0.15
        reasons.append("high_refund_ratio")
    elif refund_ratio >= 0.4:
        score += 0.08
        reasons.append("moderate_refund_ratio")

    if transfer_attempts_recent >= 5:
        score += 0.25
        reasons.append("high_transfer_attempts_extreme")
    elif transfer_attempts_recent >= 3:
        score += 0.16
        reasons.append("high_transfer_attempts")
    elif transfer_attempts_recent >= 1:
        score += 0.08
        reasons.append("moderate_transfer_attempts")

    if device_multi_account_count >= 5:
        score += 0.25
        reasons.append("device_multi_account_extreme")
    elif device_multi_account_count >= 3:
        score += 0.18
        reasons.append("device_multi_account_high")
    elif device_multi_account_count >= 2:
        score += 0.10
        reasons.append("device_multi_account_moderate")

    if high_velocity_order and device_multi_account_count >= 3:
        score += 0.20
        reasons.append("high_risk_combo_velocity_device")

    if high_velocity_order and transfer_attempts_recent >= 3:
        score += 0.15
        reasons.append("high_risk_combo_velocity_transfer")

    if same_event_order_count >= 3 and refund_ratio >= 0.6:
        score += 0.12
        reasons.append("high_risk_combo_repeat_refund")

    if device_multi_account_count >= 3 and transfer_attempts_recent >= 3:
        score += 0.18
        reasons.append("high_risk_combo_device_transfer")

    force_high = False
    if high_velocity_order and device_multi_account_count >= 4 and transfer_attempts_recent >= 5:
        force_high = True
        reasons.append("force_high_scalping_pattern")

    final_score = _cap(score)
    if force_high and final_score < 0.85:
        final_score = 0.85

    return {
        "risk_type": "scalping",
        "score": final_score,
        "reasons": reasons,
    }


def _score_abuse(signals: Dict[str, Any]) -> Dict[str, Any]:
    score = 0.0
    reasons = []

    qr_duplicate_attempts_recent = _int(signals.get("qr_duplicate_attempts_recent"))
    invalid_checkin_count_recent = _int(signals.get("invalid_checkin_count_recent"))
    chat_spam_count_recent = _int(signals.get("chat_spam_count_recent"))
    blocked_action_retry_count = _int(signals.get("blocked_action_retry_count"))
    post_refund_chat_attempt = _bool(signals.get("post_refund_chat_attempt"))
    transfer_attempts_recent = _int(signals.get("transfer_attempts_recent"))

    if qr_duplicate_attempts_recent >= 7:
        score += 0.40
        reasons.append("qr_duplicate_attempt_extreme")
    elif qr_duplicate_attempts_recent >= 4:
        score += 0.30
        reasons.append("qr_duplicate_attempt_high")
    elif qr_duplicate_attempts_recent >= 2:
        score += 0.18
        reasons.append("qr_duplicate_attempt")
    elif qr_duplicate_attempts_recent >= 1:
        score += 0.08
        reasons.append("qr_duplicate_attempt_low")

    if invalid_checkin_count_recent >= 6:
        score += 0.30
        reasons.append("invalid_checkin_extreme")
    elif invalid_checkin_count_recent >= 3:
        score += 0.20
        reasons.append("invalid_checkin_high")
    elif invalid_checkin_count_recent >= 1:
        score += 0.10
        reasons.append("invalid_checkin")

    if chat_spam_count_recent > 10:
        score += 0.30
        reasons.append("chat_spam_behavior_extreme")
    elif chat_spam_count_recent >= 6:
        score += 0.18
        reasons.append("chat_spam_behavior_high")
    elif chat_spam_count_recent >= 3:
        score += 0.08
        reasons.append("chat_spam_behavior")

    if blocked_action_retry_count >= 5:
        score += 0.25
        reasons.append("blocked_action_retry_extreme")
    elif blocked_action_retry_count >= 3:
        score += 0.20
        reasons.append("blocked_action_retry")

    if post_refund_chat_attempt:
        score += 0.18
        reasons.append("post_refund_chat_attempt")

    if transfer_attempts_recent >= 3:
        score += 0.10
        reasons.append("high_transfer_attempts")

    if qr_duplicate_attempts_recent >= 3 and invalid_checkin_count_recent >= 3:
        score += 0.15
        reasons.append("high_risk_combo_duplicate_invalid_checkin")

    if chat_spam_count_recent >= 6 and blocked_action_retry_count >= 3:
        score += 0.15
        reasons.append("high_risk_combo_spam_retry")

    if post_refund_chat_attempt and transfer_attempts_recent >= 2:
        score += 0.12
        reasons.append("high_risk_combo_post_refund_transfer")

    force_high = False
    if qr_duplicate_attempts_recent >= 5 and invalid_checkin_count_recent >= 3:
        force_high = True
        reasons.append("force_high_abuse_pattern")

    final_score = _cap(score)
    if force_high and final_score < 0.82:
        final_score = 0.82

    return {
        "risk_type": "abuse",
        "score": final_score,
        "reasons": reasons,
    }


def _pick_top_risk_type(results: list[Dict[str, Any]]) -> Dict[str, Any]:
    priority = {
        "account_takeover": 3,
        "abuse": 2,
        "scalping": 1,
    }

    results = sorted(
        results,
        key=lambda x: (x["score"], priority.get(x["risk_type"], 0)),
        reverse=True,
    )
    return results[0]


def evaluate_fraud_service(sb, payload: Dict[str, Any]) -> Dict[str, Any]:
    order = None

    if payload.get("order_id"):
        base = _build_base_context_from_order(sb, payload["order_id"])
        order = base.get("order")
        ctx = {
            **base,
            "user_id": payload.get("user_id") or base.get("user_id"),
            "event_uuid": payload.get("event_uuid") or base.get("event_uuid"),
            "qty": payload.get("qty") if payload.get("qty") is not None else base.get("qty"),
            "total_amount": payload.get("total_amount") if payload.get("total_amount") is not None else base.get("total_amount"),
        }
    else:
        ctx = {
            "order_id": None,
            "user_id": payload.get("user_id"),
            "event_uuid": payload.get("event_uuid"),
            "qty": payload.get("qty") or 0,
            "total_amount": float(payload.get("total_amount") or 0),
        }

    db_signals = _collect_db_signals(sb, ctx)
    signals = _merge_external_signals(db_signals, payload)

    risk_candidates = [
        _score_account_takeover(signals),
        _score_scalping(signals),
        _score_abuse(signals),
    ]
    top_risk = _pick_top_risk_type(risk_candidates)

    raw_risk_score = round(float(top_risk["score"]), 4)
    risk_type = top_risk["risk_type"]
    reasons = top_risk["reasons"]

    reference_ts = _extract_reference_risk_time(payload, order=order)
    decay_info = _apply_score_decay(
        raw_score=raw_risk_score,
        reference_ts=reference_ts,
        severe=_is_severe_risk_type(risk_type),
    )

    risk_score = float(decay_info["risk_score"])
    risk_level = _score_to_level(risk_score)

    return {
        "order_id": ctx.get("order_id"),
        "user_id": ctx.get("user_id"),
        "risk_score": risk_score,
        "raw_risk_score": float(decay_info["raw_risk_score"]),
        "risk_level": risk_level,
        "risk_type": risk_type,
        "reasons": reasons,
        "signals": signals,
        "recommended_action": _recommended_action(risk_level, risk_type),
        "order": order,
        "last_risk_at": reference_ts.isoformat() if reference_ts else None,
        "decay_applied": bool(decay_info["decay_applied"]),
        "decay_factor": float(decay_info["decay_factor"]),
        "days_since_risk": float(decay_info["days_since_risk"]),
    }


def check_order_fraud_service(sb, order_id: str):
    result = evaluate_fraud_service(sb, {"order_id": order_id})
    return {
        "order_id": result["order_id"],
        "user_id": result["user_id"],
        "risk_score": result["risk_score"],
        "raw_risk_score": result["raw_risk_score"],
        "risk_level": result["risk_level"],
        "risk_type": result["risk_type"],
        "reasons": result["reasons"],
        "signals": result["signals"],
        "recommended_action": result["recommended_action"],
        "last_risk_at": result.get("last_risk_at"),
        "decay_applied": result.get("decay_applied", False),
        "decay_factor": result.get("decay_factor", 1.0),
        "days_since_risk": result.get("days_since_risk", 0.0),
    }


def get_order_fraud_detail_service(sb, order_id: str):
    result = evaluate_fraud_service(sb, {"order_id": order_id})
    return {
        "order": result.get("order"),
        "fraud": {
            "order_id": result["order_id"],
            "user_id": result["user_id"],
            "risk_score": result["risk_score"],
            "raw_risk_score": result["raw_risk_score"],
            "risk_level": result["risk_level"],
            "risk_type": result["risk_type"],
            "reasons": result["reasons"],
            "signals": result["signals"],
            "recommended_action": result["recommended_action"],
            "last_risk_at": result.get("last_risk_at"),
            "decay_applied": result.get("decay_applied", False),
            "decay_factor": result.get("decay_factor", 1.0),
            "days_since_risk": result.get("days_since_risk", 0.0),
        },
    }