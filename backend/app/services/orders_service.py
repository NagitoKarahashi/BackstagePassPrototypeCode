from fastapi import HTTPException
from app.services.profiles_service import resolve_internal_user_id
from app.services.rewards_service import handle_order_reward
from app.services.risk_service import (
    evaluate_risk_context,
    should_block_order,
    should_require_extra_verification,
)


def create_order_service(
    sb,
    external_auth_id: str,
    event_id: str,
    quantity: int,
    device_id: str | None = None,
    ip_address: str | None = None,
):
    internal_user_id = resolve_internal_user_id(sb, external_auth_id)

    risk_ctx = evaluate_risk_context(
        sb,
        {
            "user_id": str(internal_user_id),
            "event_uuid": event_id,
            "qty": quantity,
            "device_id": device_id,
            "ip_address": ip_address,
        },
        lang="en",
    )

    if should_block_order(risk_ctx):
        raise HTTPException(
            status_code=403,
            detail={
                "message": "Order creation is temporarily restricted due to elevated risk signals.",
                "risk_level": risk_ctx["risk_level"],
                "risk_type": risk_ctx["risk_type"],
                "recommended_action": risk_ctx["recommended_action"],
                "reasons": risk_ctx["reasons"],
            },
        )

    try:
        res = sb.rpc(
            "create_order_atomic",
            {
                "p_user_id": str(internal_user_id),
                "p_event_uuid": event_id,
                "p_qty": quantity,
            }
        ).execute()

        if not res.data:
            raise HTTPException(status_code=400, detail="Failed to create order")

        data = res.data
        if isinstance(data, list):
            if not data:
                raise HTTPException(status_code=400, detail="Empty create_order_atomic response")
            data = data[0]

        if not isinstance(data, dict):
            raise HTTPException(
                status_code=400,
                detail=f"Unexpected create_order_atomic response shape: {data}"
            )

        return {
            "order_id": data.get("order_id"),
            "user_id": data.get("user_id"),
            "event_id": data.get("event_id"),
            "event_uuid": data.get("event_uuid"),
            "qty": data.get("qty"),
            "total_amount": data.get("total_amount"),
            "status": data.get("status"),
            "risk": {
                "risk_score": risk_ctx["risk_score"],
                "risk_level": risk_ctx["risk_level"],
                "risk_type": risk_ctx["risk_type"],
                "reasons": risk_ctx["reasons"],
                "recommended_action": risk_ctx["recommended_action"],
                "review_required": should_require_extra_verification(risk_ctx),
            },
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


def pay_order_service(sb, order_id):
    try:
        res = sb.rpc(
            "pay_order_and_issue_tickets",
            {
                "p_order_id": order_id,
            }
        ).execute()

        if not res.data:
            raise HTTPException(status_code=400, detail="Failed to pay order")

        result = res.data
        if isinstance(result, list):
            result = result[0] if result else None

        if not isinstance(result, dict):
            return result

        paid_order_id = result.get("order_id", order_id)
        internal_user_id = result.get("user_id")
        reward_result = {
            "triggered": False,
            "warning": None,
        }

        if not internal_user_id:
            try:
                order_resp = (
                    sb.table("orders")
                    .select("id, user_id, status")
                    .eq("id", paid_order_id)
                    .limit(1)
                    .execute()
                )
                order_row = order_resp.data[0] if order_resp.data else None
                if order_row:
                    internal_user_id = order_row.get("user_id")
            except Exception as e:
                reward_result["warning"] = f"Reward lookup failed: {str(e)}"

        if internal_user_id:
            try:
                handle_order_reward(
                    sb=sb,
                    internal_user_id=str(internal_user_id),
                    order_id=str(paid_order_id),
                )
                reward_result["triggered"] = True
            except Exception as e:
                reward_result["warning"] = f"Reward trigger failed: {str(e)}"
        else:
            reward_result["warning"] = "Reward skipped: user_id missing after payment"

        result["reward"] = reward_result
        return result

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))   


def cancel_order_service(sb, order_id):
    try:
        res = sb.rpc(
            "cancel_order_and_restore_stock",
            {
                "p_order_id": order_id,
            }
        ).execute()

        if not res.data:
            raise HTTPException(status_code=400, detail="Failed to cancel order")

        return res.data

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))