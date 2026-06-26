from typing import Any, Dict, Optional


def _contains_any(text: str, keywords: list[str]) -> bool:
    t = (text or "").lower()
    return any(k.lower() in t for k in keywords)


def _build_refund_support(question: str, context: Dict[str, Any], lang: str) -> Optional[Dict[str, Any]]:
    q = question.lower()

    refund_keywords = [
        "refund", "refunded", "refund status", "money back",
        "退票", "退款", "退回", "退钱", "退费",
    ]
    if not _contains_any(q, refund_keywords):
        return None

    order = context.get("order") or {}
    ticket = context.get("ticket") or {}
    refund = context.get("refund") or {}

    order_status = (order.get("status") or "").lower()
    ticket_status = (ticket.get("status") or "").lower()
    refund_status = (refund.get("status") or "").lower()

    if refund_status in {"approved", "completed", "refunded"}:
        answer = (
            "该订单/票券的退款已经完成。你可以在订单记录或钱包页确认最终状态；若金额未到账，请再检查支付渠道的到账时间。"
            if lang == "zh"
            else "The refund for this order/ticket has already been completed. Please check your order history or wallet for the final status, and allow additional time for the payment channel to process the refund."
        )
        return {"answer": answer, "source": "support://refund/completed", "score": 0.98}

    if refund_status in {"pending", "processing"}:
        answer = (
            "你的退款申请正在处理中。目前不建议重复提交申请。你可以在订单详情页查看最新退款状态。"
            if lang == "zh"
            else "Your refund request is currently being processed. It is not recommended to submit another request. Please check the order detail page for the latest refund status."
        )
        return {"answer": answer, "source": "support://refund/pending", "score": 0.96}

    if ticket_status == "used":
        answer = (
            "该票券状态已为 used，通常已使用的票券不能退款。若你认为状态异常，需要人工复核。"
            if lang == "zh"
            else "This ticket is already marked as used. Used tickets are typically not eligible for refund. If you believe this status is incorrect, manual review is required."
        )
        return {"answer": answer, "source": "support://refund/ticket-used", "score": 0.97}

    if ticket_status == "expired":
        answer = (
            "该票券已过期。过期票券通常不支持退款，具体仍以平台退款规则为准。"
            if lang == "zh"
            else "This ticket is already expired. Expired tickets are usually not refundable, subject to the platform refund policy."
        )
        return {"answer": answer, "source": "support://refund/ticket-expired", "score": 0.94}

    if order_status in {"cancelled", "canceled"}:
        answer = (
            "该订单当前已取消。如果系统尚未显示退款结果，请检查是否仍在退款处理流程中。"
            if lang == "zh"
            else "This order has already been cancelled. If the refund is not yet visible, please check whether it is still being processed."
        )
        return {"answer": answer, "source": "support://refund/order-cancelled", "score": 0.93}

    if order_status == "paid":
        answer = (
            "该订单当前为 paid 状态。是否可退款取决于平台规则、活动时间节点以及票券状态。你可以发起退款申请，系统会根据状态校验是否允许退款。"
            if lang == "zh"
            else "This order is currently in paid status. Refund eligibility depends on platform policy, event timing, and ticket state. You may submit a refund request and the system will validate whether it is allowed."
        )
        return {"answer": answer, "source": "support://refund/order-paid", "score": 0.90}

    return None


def _build_wallet_support(question: str, context: Dict[str, Any], lang: str) -> Optional[Dict[str, Any]]:
    q = question.lower()

    wallet_keywords = [
        "wallet", "my ticket", "ticket not showing", "qr", "qr code",
        "钱包", "票券", "门票", "二维码", "看不到票", "票没显示",
    ]
    if not _contains_any(q, wallet_keywords):
        return None

    ticket = context.get("ticket") or {}
    order = context.get("order") or {}

    ticket_status = (ticket.get("status") or "").lower()
    qr_payload = ticket.get("qr_payload")
    order_status = (order.get("status") or "").lower()

    if order_status in {"pending", "created"}:
        answer = (
            "该订单尚未完成支付，因此票券可能还未生成，也不会出现在钱包中。请先完成支付。"
            if lang == "zh"
            else "This order has not been fully paid yet, so the ticket may not have been issued and will not appear in the wallet. Please complete payment first."
        )
        return {"answer": answer, "source": "support://wallet/unpaid-order", "score": 0.97}

    if not ticket and order_status == "paid":
        answer = (
            "订单已支付，但当前上下文中还没有票券信息。这通常表示出票尚未同步完成，建议稍后刷新钱包页；若长时间仍未出现，需要排查出票流程。"
            if lang == "zh"
            else "The order has been paid, but no ticket information is available in the current context. This usually means ticket issuance has not yet synced. Please refresh the wallet later; if it still does not appear, the issuance flow should be checked."
        )
        return {"answer": answer, "source": "support://wallet/ticket-sync-delay", "score": 0.94}

    if ticket_status == "active" and qr_payload:
        answer = (
            "你的票券当前为 active 状态，二维码应可正常显示并用于入场。"
            if lang == "zh"
            else "Your ticket is currently active, and the QR code should be available for entry."
        )
        return {"answer": answer, "source": "support://wallet/active-ticket", "score": 0.98}

    if ticket_status == "used":
        answer = (
            "你的票券状态为 used，说明该二维码通常已经完成检票，因此不能再次作为有效入场凭证。"
            if lang == "zh"
            else "Your ticket is marked as used, which usually means the QR code has already been scanned and can no longer be used as a valid entry credential."
        )
        return {"answer": answer, "source": "support://wallet/used-ticket", "score": 0.98}

    if ticket_status == "expired":
        answer = (
            "你的票券状态为 expired。过期票券通常不能再次使用，二维码也可能不再有效。"
            if lang == "zh"
            else "Your ticket is marked as expired. Expired tickets generally cannot be used again, and the QR code may no longer be valid."
        )
        return {"answer": answer, "source": "support://wallet/expired-ticket", "score": 0.97}

    return None


def _build_chat_support(question: str, context: Dict[str, Any], lang: str) -> Optional[Dict[str, Any]]:
    q = question.lower()

    chat_keywords = [
        "chat", "chat room", "message", "send message", "community",
        "聊天室", "聊天", "发消息", "不能聊天", "进不去聊天室", "社区",
    ]
    if not _contains_any(q, chat_keywords):
        return None

    ticket = context.get("ticket") or {}
    refund = context.get("refund") or {}
    chat = context.get("chat") or {}

    ticket_status = (ticket.get("status") or "").lower()
    refund_status = (refund.get("status") or "").lower()
    chat_access = chat.get("has_access")

    if refund_status in {"approved", "completed", "refunded"}:
        answer = (
            "如果该订单已经完成退款，通常应撤销对应活动聊天室的访问权限。若你仍然能发言或仍然被错误拦截，就需要检查退款状态和聊天室权限同步。"
            if lang == "zh"
            else "If the order has already been refunded, access to the related event chat room should usually be removed. If you can still post or are still blocked incorrectly, the refund state and chat permission linkage should be checked."
        )
        return {"answer": answer, "source": "support://chat/refund-linkage", "score": 0.99}

    if chat_access is False:
        answer = (
            "你当前没有聊天室访问权限。通常只有持有有效活动票券的用户才能访问对应聊天室。请检查票券状态和所属活动是否一致。"
            if lang == "zh"
            else "You currently do not have chat room access. Usually only users with a valid ticket for the related event can access that room. Please check whether the ticket status and event match."
        )
        return {"answer": answer, "source": "support://chat/no-access", "score": 0.97}

    if ticket_status in {"active", "used"} and chat_access is True:
        answer = (
            "你当前应具备该活动聊天室的访问资格。如果前端仍显示无权限，更可能是权限同步或页面状态缓存问题。"
            if lang == "zh"
            else "You should currently be eligible to access the event chat room. If the frontend still shows no permission, it is more likely a permission sync issue or stale page state."
        )
        return {"answer": answer, "source": "support://chat/should-have-access", "score": 0.96}

    return None


def _build_order_support(question: str, context: Dict[str, Any], lang: str) -> Optional[Dict[str, Any]]:
    q = question.lower()

    order_keywords = [
        "order", "booking", "payment", "paid", "cancelled", "canceled",
        "订单", "支付", "付款", "购票", "已支付", "取消订单",
    ]
    if not _contains_any(q, order_keywords):
        return None

    order = context.get("order") or {}
    ticket = context.get("ticket") or {}

    order_status = (order.get("status") or "").lower()
    ticket_status = (ticket.get("status") or "").lower()

    if order_status in {"pending", "created"}:
        answer = (
            "订单目前还处于待支付/刚创建状态，后续是否生成票券取决于支付是否完成。"
            if lang == "zh"
            else "The order is still in a pending/newly created state. Whether tickets are generated depends on whether payment is completed."
        )
        return {"answer": answer, "source": "support://order/pending", "score": 0.95}

    if order_status == "paid" and not ticket:
        answer = (
            "订单已支付，但票券信息还未进入当前上下文。这通常意味着出票结果还未同步到前端。"
            if lang == "zh"
            else "The order has been paid, but ticket information is not yet available in the current context. This usually means ticket issuance has not yet synced to the frontend."
        )
        return {"answer": answer, "source": "support://order/paid-no-ticket", "score": 0.94}

    if order_status == "paid" and ticket_status == "active":
        answer = (
            "订单已支付且票券已激活，当前应该可以在钱包中查看票券并显示二维码。"
            if lang == "zh"
            else "The order has been paid and the ticket is active. It should now be visible in the wallet and display a QR code."
        )
        return {"answer": answer, "source": "support://order/paid-active-ticket", "score": 0.97}

    if order_status in {"cancelled", "canceled"}:
        answer = (
            "订单已取消。后续是否有退款结果，需要结合退款状态一并确认。"
            if lang == "zh"
            else "The order has been cancelled. Whether there is a refund result should be confirmed together with the refund status."
        )
        return {"answer": answer, "source": "support://order/cancelled", "score": 0.95}

    return None


def answer_support_question(question: str, context: Dict[str, Any], lang: str) -> Optional[Dict[str, Any]]:
    """
    Support-first business explanation layer.
    Returns:
      {
        "answer": str,
        "source": str,
        "score": float
      }
    or None
    """
    builders = [
        _build_refund_support,
        _build_wallet_support,
        _build_chat_support,
        _build_order_support,
    ]

    for builder in builders:
        result = builder(question, context, lang)
        if result:
            return result

    return None