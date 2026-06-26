from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


HIGH_RISK_REASON_LABELS = {
    "rapid_repeat_orders": "high-frequency repeated orders",
    "multi_device_switching": "frequent device switching",
    "high_refund_ratio": "an unusually high refund ratio",
    "suspicious_transfer_pattern": "unusual ticket transfer behavior",
    "abnormal_checkin_pattern": "abnormal check-in pattern",
    "chat_spam_behavior": "abnormal chat activity",
}

HIGH_RISK_REASON_LABELS.update({
    "device_multi_account_extreme": "extreme multi-account use on one device",
    "device_multi_account_high": "high multi-account use on one device",
    "device_multi_account_moderate": "moderate multi-account use on one device",
    "high_risk_combo_location_wallet": "location mismatch combined with wallet reuse",
    "high_risk_combo_location_device": "location mismatch combined with multi-account device usage",
    "high_risk_combo_wallet_transfer": "wallet reuse combined with suspicious transfer attempts",
    "high_risk_combo_location_transfer": "location mismatch combined with suspicious transfer attempts",
    "force_high_account_takeover_pattern": "strong account takeover pattern",

    "multiple_recent_orders_extreme": "extreme recent order volume",
    "multiple_recent_orders_high": "high recent order volume",
    "repeat_orders_same_event_extreme": "extreme repeated orders for the same event",
    "repeat_orders_same_event_high": "high repeated orders for the same event",
    "high_refund_ratio_extreme": "extremely high refund ratio",
    "moderate_transfer_attempts": "moderate transfer attempts",
    "high_transfer_attempts_extreme": "extremely frequent transfer attempts",
    "high_risk_combo_velocity_device": "high order velocity combined with multi-account device usage",
    "high_risk_combo_velocity_transfer": "high order velocity combined with frequent transfer attempts",
    "high_risk_combo_repeat_refund": "repeated same-event orders combined with high refund ratio",
    "high_risk_combo_device_transfer": "multi-account device usage combined with frequent transfer attempts",
    "force_high_scalping_pattern": "strong scalping pattern",

    "qr_duplicate_attempt_extreme": "extreme duplicate QR attempts",
    "qr_duplicate_attempt_high": "high duplicate QR attempts",
    "qr_duplicate_attempt_low": "low-level duplicate QR attempts",
    "invalid_checkin_extreme": "extreme invalid check-in attempts",
    "invalid_checkin_high": "high invalid check-in attempts",
    "invalid_checkin": "invalid check-in attempts",
    "chat_spam_behavior_extreme": "extreme chat spam behavior",
    "chat_spam_behavior_high": "high chat spam behavior",
    "blocked_action_retry_extreme": "extreme retry attempts after restriction",
    "blocked_action_retry": "retry attempts after restriction",
    "post_refund_chat_attempt": "chat attempts after refund",
    "high_risk_combo_duplicate_invalid_checkin": "duplicate and invalid check-in pattern",
    "high_risk_combo_spam_retry": "chat spam combined with repeated restricted retries",
    "high_risk_combo_post_refund_transfer": "post-refund chat attempts combined with transfer attempts",
    "force_high_abuse_pattern": "strong platform abuse pattern",
})

HIGH_RISK_REASON_LABELS_ZH = {
    "rapid_repeat_orders": "短时间高频下单",
    "multi_device_switching": "频繁切换设备",
    "high_refund_ratio": "退款比例异常偏高",
    "suspicious_transfer_pattern": "转票行为异常",
    "abnormal_checkin_pattern": "检票行为异常",
    "chat_spam_behavior": "聊天行为异常",
}

HIGH_RISK_REASON_LABELS_ZH.update({
    "device_multi_account_extreme": "单设备极端多账号使用",
    "device_multi_account_high": "单设备高频多账号使用",
    "device_multi_account_moderate": "单设备中度多账号使用",
    "high_risk_combo_location_wallet": "异地行为与钱包复用同时出现",
    "high_risk_combo_location_device": "异地行为与多账号共设备同时出现",
    "high_risk_combo_wallet_transfer": "钱包复用与异常转票尝试同时出现",
    "high_risk_combo_location_transfer": "异地行为与异常转票尝试同时出现",
    "force_high_account_takeover_pattern": "强账号盗用特征组合",

    "multiple_recent_orders_extreme": "近期订单量极高",
    "multiple_recent_orders_high": "近期订单量偏高",
    "repeat_orders_same_event_extreme": "同活动重复下单极高",
    "repeat_orders_same_event_high": "同活动重复下单偏高",
    "high_refund_ratio_extreme": "退款比例极高",
    "moderate_transfer_attempts": "转票尝试偏多",
    "high_transfer_attempts_extreme": "转票尝试极高",
    "high_risk_combo_velocity_device": "高频下单与多账号共设备同时出现",
    "high_risk_combo_velocity_transfer": "高频下单与频繁转票尝试同时出现",
    "high_risk_combo_repeat_refund": "同活动重复下单与高退款比例同时出现",
    "high_risk_combo_device_transfer": "多账号共设备与频繁转票尝试同时出现",
    "force_high_scalping_pattern": "强黄牛/倒票特征组合",

    "qr_duplicate_attempt_extreme": "二维码重复尝试极高",
    "qr_duplicate_attempt_high": "二维码重复尝试偏高",
    "qr_duplicate_attempt_low": "轻度二维码重复尝试",
    "invalid_checkin_extreme": "无效检票尝试极高",
    "invalid_checkin_high": "无效检票尝试偏高",
    "invalid_checkin": "无效检票尝试",
    "chat_spam_behavior_extreme": "聊天刷屏行为极高",
    "chat_spam_behavior_high": "聊天刷屏行为偏高",
    "blocked_action_retry_extreme": "受限后重复尝试极高",
    "blocked_action_retry": "受限后重复尝试",
    "post_refund_chat_attempt": "退款后仍尝试聊天",
    "high_risk_combo_duplicate_invalid_checkin": "重复检票与无效检票组合异常",
    "high_risk_combo_spam_retry": "刷屏与重复违规尝试组合异常",
    "high_risk_combo_post_refund_transfer": "退款后聊天尝试与转票尝试组合异常",
    "force_high_abuse_pattern": "强平台滥用特征组合",
})


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


def _normalize_risk_level(level: Optional[str]) -> str:
    level = (level or "").lower()
    if level in {"high", "medium", "low"}:
        return level
    return "low"


def _infer_risk_level_from_score(score: Optional[float]) -> str:
    if score is None:
        return "low"
    if score >= 0.75:
        return "high"
    if score >= 0.4:
        return "medium"
    return "low"


def _format_reasons(reasons: List[str], lang: str) -> str:
    if not reasons:
        return ""

    if lang == "zh":
        labels = [HIGH_RISK_REASON_LABELS_ZH.get(r, r) for r in reasons]
        return "、".join(labels)

    labels = [HIGH_RISK_REASON_LABELS.get(r, r.replace("_", " ")) for r in reasons]
    return ", ".join(labels)


def _build_user_message(
    risk_level: str,
    reasons: List[str],
    lang: str,
) -> Optional[str]:
    if risk_level == "low":
        return None

    reason_text = _format_reasons(reasons, lang)

    if lang == "zh":
        if risk_level == "high":
            if reason_text:
                return (
                    f"系统检测到较高风险信号（{reason_text}）。"
                    "为保障票务与账号安全，部分操作可能被限制，必要时需要人工审核。"
                )
            return "系统检测到较高风险信号。为保障票务与账号安全，部分操作可能被限制，必要时需要人工审核。"

        if risk_level == "medium":
            if reason_text:
                return (
                    f"系统检测到一定风险信号（{reason_text}）。"
                    "建议避免异常购票、频繁退款或非官方转票操作，以免触发更严格限制。"
                )
            return "系统检测到一定风险信号。建议避免异常购票、频繁退款或非官方转票操作，以免触发更严格限制。"

    else:
        if risk_level == "high":
            if reason_text:
                return (
                    f"Our system detected high-risk signals ({reason_text}). "
                    "To protect ticketing and account security, some actions may be restricted and manual review may be required."
                )
            return (
                "Our system detected high-risk signals. "
                "To protect ticketing and account security, some actions may be restricted and manual review may be required."
            )

        if risk_level == "medium":
            if reason_text:
                return (
                    f"Our system detected some risk signals ({reason_text}). "
                    "Please avoid unusual purchase, refund, or unofficial transfer behavior to prevent stricter limitations."
                )
            return (
                "Our system detected some risk signals. "
                "Please avoid unusual purchase, refund, or unofficial transfer behavior to prevent stricter limitations."
            )

    return None


def _build_recommended_action(risk_level: str) -> str:
    if risk_level == "high":
        return "manual_review"
    if risk_level == "medium":
        return "additional_verification"
    return "allow"


def _extract_existing_risk(context: Dict[str, Any]) -> Dict[str, Any]:
    risk = context.get("risk") or {}
    score = risk.get("risk_score")
    level = (
        _normalize_risk_level(risk.get("risk_level"))
        if risk.get("risk_level")
        else _infer_risk_level_from_score(score)
    )
    reasons = risk.get("reasons") or []
    return {
        "risk_score": float(score if score is not None else 0.0),
        "raw_risk_score": float(risk.get("raw_risk_score") or score or 0.0),
        "risk_level": level,
        "risk_type": risk.get("risk_type") or "none",
        "reasons": reasons,
        "signals": risk.get("signals") or {},
        "last_risk_at": risk.get("last_risk_at"),
        "decay_applied": bool(risk.get("decay_applied", False)),
        "decay_factor": float(risk.get("decay_factor") or 1.0),
        "days_since_risk": float(risk.get("days_since_risk") or 0.0),
    }


def _try_compute_risk_from_fraud_service(context: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    try:
        from app.services.fraud_service import evaluate_fraud_service  # type: ignore
    except Exception:
        return None

    sb = context.get("_sb")
    if sb is None:
        return None

    payload = {
        "user_id": context.get("user_id") or (context.get("user") or {}).get("id"),
        "order_id": context.get("order_id") or (context.get("order") or {}).get("id"),
        "event_uuid": context.get("event_uuid") or (context.get("order") or {}).get("event_uuid"),
        "qty": context.get("qty") or (context.get("order") or {}).get("qty"),
        "device_id": context.get("device_id") or (context.get("device") or {}).get("device_id"),
        "ip_address": context.get("ip_address") or (context.get("device") or {}).get("ip_address"),
        "last_risk_at": context.get("last_risk_at") or (context.get("risk") or {}).get("last_risk_at"),
        "risk_updated_at": context.get("risk_updated_at") or (context.get("risk") or {}).get("risk_updated_at"),
        "latest_signal_at": context.get("latest_signal_at") or (context.get("risk") or {}).get("latest_signal_at"),
        "latest_abnormal_at": context.get("latest_abnormal_at") or (context.get("risk") or {}).get("latest_abnormal_at"),
    }

    try:
        result = evaluate_fraud_service(sb, payload)
    except Exception:
        return None

    if not isinstance(result, dict):
        return None

    score = result.get("risk_score")
    raw_score = result.get("raw_risk_score")
    level = result.get("risk_level")
    reasons = result.get("reasons") or []

    return {
        "risk_score": float(score if score is not None else 0.0),
        "raw_risk_score": float(raw_score if raw_score is not None else score or 0.0),
        "risk_level": _normalize_risk_level(level) if level else _infer_risk_level_from_score(score),
        "risk_type": result.get("risk_type") or "none",
        "reasons": reasons,
        "signals": result.get("signals") or {},
        "last_risk_at": result.get("last_risk_at"),
        "decay_applied": bool(result.get("decay_applied", False)),
        "decay_factor": float(result.get("decay_factor") or 1.0),
        "days_since_risk": float(result.get("days_since_risk") or 0.0),
        "recommended_action": result.get("recommended_action"),
    }


def build_risk_context(context: Dict[str, Any], lang: str = "en") -> Dict[str, Any]:
    existing = _extract_existing_risk(context)
    if (
        existing["risk_score"]
        or existing["raw_risk_score"]
        or existing["risk_level"] != "low"
        or existing["reasons"]
    ):
        risk_data = existing
    else:
        computed = _try_compute_risk_from_fraud_service(context)
        risk_data = computed or existing

    risk_level = _normalize_risk_level(risk_data.get("risk_level"))
    risk_score = float(risk_data.get("risk_score") or 0.0)
    raw_risk_score = float(risk_data.get("raw_risk_score") or risk_score or 0.0)
    reasons = risk_data.get("reasons") or []

    return {
        "risk_level": risk_level,
        "risk_score": risk_score,
        "raw_risk_score": raw_risk_score,
        "risk_type": risk_data.get("risk_type") or "none",
        "reasons": reasons,
        "signals": risk_data.get("signals") or {},
        "last_risk_at": risk_data.get("last_risk_at"),
        "decay_applied": bool(risk_data.get("decay_applied", False)),
        "decay_factor": float(risk_data.get("decay_factor") or 1.0),
        "days_since_risk": float(risk_data.get("days_since_risk") or 0.0),
        "user_message": _build_user_message(risk_level, reasons, lang),
        "recommended_action": risk_data.get("recommended_action") or _build_recommended_action(risk_level),
    }


def apply_risk_policy(
    intent: str,
    risk_ctx: Dict[str, Any],
) -> Dict[str, Any]:
    risk_level = risk_ctx.get("risk_level", "low")

    block_intents_for_high_risk = {"transfer"}
    cautious_intents = {"refund", "transfer", "event_search", "other"}

    hard_block = risk_level == "high" and intent in block_intents_for_high_risk
    caution = risk_level in {"medium", "high"} and intent in cautious_intents

    return {
        "hard_block": hard_block,
        "caution": caution,
        "recommended_action": risk_ctx.get("recommended_action", "allow"),
    }


def build_block_message(intent: str, lang: str) -> str:
    if lang == "zh":
        if intent == "transfer":
            return "由于当前账号存在较高风险信号，转票相关操作暂时受到限制。若需继续处理，请联系人工客服或提交申诉。"
        return "由于当前账号存在较高风险信号，相关操作暂时受到限制。请联系人工客服或提交申诉。"

    if intent == "transfer":
        return (
            "Because the current account shows high-risk signals, ticket transfer-related actions are temporarily restricted. "
            "Please contact support or submit an appeal if you need further help."
        )
    return (
        "Because the current account shows high-risk signals, the related action is temporarily restricted. "
        "Please contact support or submit an appeal if you need further help."
    )


def build_risk_context_from_result(result: Optional[Dict[str, Any]], lang: str = "en") -> Dict[str, Any]:
    if not result:
        return {
            "risk_level": "low",
            "risk_score": 0.0,
            "raw_risk_score": 0.0,
            "risk_type": "none",
            "reasons": [],
            "signals": {},
            "last_risk_at": None,
            "decay_applied": False,
            "decay_factor": 1.0,
            "days_since_risk": 0.0,
            "user_message": None,
            "recommended_action": "allow",
        }

    risk_level = _normalize_risk_level(result.get("risk_level"))
    risk_score = float(result.get("risk_score") or 0.0)
    raw_risk_score = float(result.get("raw_risk_score") or risk_score or 0.0)
    risk_type = result.get("risk_type") or "none"
    reasons = result.get("reasons") or []
    signals = result.get("signals") or {}
    recommended_action = result.get("recommended_action") or _build_recommended_action(risk_level)

    return {
        "risk_level": risk_level,
        "risk_score": risk_score,
        "raw_risk_score": raw_risk_score,
        "risk_type": risk_type,
        "reasons": reasons,
        "signals": signals,
        "last_risk_at": result.get("last_risk_at"),
        "decay_applied": bool(result.get("decay_applied", False)),
        "decay_factor": float(result.get("decay_factor") or 1.0),
        "days_since_risk": float(result.get("days_since_risk") or 0.0),
        "user_message": _build_user_message(risk_level, reasons, lang),
        "recommended_action": recommended_action,
    }


def evaluate_risk_context(sb, payload: Dict[str, Any], lang: str = "en") -> Dict[str, Any]:
    try:
        from app.services.fraud_service import evaluate_fraud_service  # type: ignore
    except Exception:
        return build_risk_context(payload, lang=lang)

    try:
        result = evaluate_fraud_service(sb, payload)
    except Exception:
        return build_risk_context(payload, lang=lang)

    return build_risk_context_from_result(result, lang=lang)


def should_block_order(risk_ctx: Dict[str, Any]) -> bool:
    return risk_ctx.get("risk_level") == "high" and risk_ctx.get("recommended_action") in {
        "manual_review",
        "freeze_sensitive_actions",
    }


def should_require_extra_verification(risk_ctx: Dict[str, Any]) -> bool:
    return risk_ctx.get("risk_level") == "medium"


def should_block_chat(risk_ctx: Dict[str, Any]) -> bool:
    return (
        risk_ctx.get("risk_level") == "high"
        and risk_ctx.get("risk_type") in {"abuse", "account_takeover"}
    )


def should_block_transfer_like_action(risk_ctx: Dict[str, Any]) -> bool:
    return (
        risk_ctx.get("risk_level") == "high"
        and risk_ctx.get("risk_type") in {"scalping", "account_takeover"}
    )


def should_block_refund(risk_ctx: Dict[str, Any]) -> bool:
    return (
        risk_ctx.get("risk_level") == "high"
        and risk_ctx.get("risk_type") in {"scalping", "account_takeover", "abuse"}
    )


def should_hold_refund_for_review(risk_ctx: Dict[str, Any]) -> bool:
    return risk_ctx.get("risk_level") == "medium"


def should_block_checkin(risk_ctx: Dict[str, Any]) -> bool:
    return (
        risk_ctx.get("risk_level") == "high"
        and risk_ctx.get("risk_type") in {"abuse", "account_takeover"}
    )


def should_require_manual_review_for_checkin(risk_ctx: Dict[str, Any]) -> bool:
    return risk_ctx.get("risk_level") == "medium"


def build_risk_restriction_message(action: str, lang: str = "en") -> str:
    if lang == "zh":
        mapping = {
            "refund": "由于当前账号存在较高风险信号，退款相关操作暂时受到限制。请联系人工客服或提交申诉。",
            "transfer": "由于当前账号存在较高风险信号，转票相关操作暂时受到限制。请联系人工客服或提交申诉。",
            "checkin": "由于当前账号存在较高风险信号，当前检票操作暂时受到限制，需要进一步核验。",
            "chat": "由于当前账号存在较高风险信号，聊天功能暂时受到限制。",
            "order": "由于当前账号存在较高风险信号，当前下单操作暂时受到限制。",
        }
        return mapping.get(action, "由于当前账号存在较高风险信号，相关操作暂时受到限制。")

    mapping = {
        "refund": "Because the current account shows high-risk signals, refund-related actions are temporarily restricted. Please contact support or submit an appeal.",
        "transfer": "Because the current account shows high-risk signals, ticket transfer-related actions are temporarily restricted. Please contact support or submit an appeal.",
        "checkin": "Because the current account shows high-risk signals, this check-in action is temporarily restricted and requires further verification.",
        "chat": "Because the current account shows high-risk signals, chat access is temporarily restricted.",
        "order": "Because the current account shows high-risk signals, order creation is temporarily restricted.",
    }
    return mapping.get(action, "Because the current account shows high-risk signals, the related action is temporarily restricted.")