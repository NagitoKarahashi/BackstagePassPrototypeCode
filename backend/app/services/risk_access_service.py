from typing import Any, Dict
from app.services.risk_service import evaluate_risk_context


def evaluate_risk_summary_service(
    sb,
    payload: Dict[str, Any],
    lang: str = "en",
) -> Dict[str, Any]:
    risk_ctx = evaluate_risk_context(sb, payload, lang=lang)
    return {
        "risk_score": risk_ctx["risk_score"],
        "raw_risk_score": risk_ctx.get("raw_risk_score", risk_ctx["risk_score"]),
        "risk_level": risk_ctx["risk_level"],
        "risk_type": risk_ctx["risk_type"],
        "reasons": risk_ctx["reasons"],
        "signals": risk_ctx["signals"],
        "recommended_action": risk_ctx["recommended_action"],
        "user_message": risk_ctx["user_message"],
        "last_risk_at": risk_ctx.get("last_risk_at"),
        "decay_applied": risk_ctx.get("decay_applied", False),
        "decay_factor": risk_ctx.get("decay_factor", 1.0),
        "days_since_risk": risk_ctx.get("days_since_risk", 0.0),
    }


def get_user_risk_summary_service(
    sb,
    user_id: str,
    lang: str = "en",
) -> Dict[str, Any]:
    return evaluate_risk_summary_service(
        sb,
        {
            "user_id": user_id,
        },
        lang=lang,
    )