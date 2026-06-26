import re
from typing import Any, Dict, List

from app.schemas.ask import AskRequest
from app.services.intent_service import (
    detect_language,
    correct_spelling_en,
    normalize_question,
    classify_intent,
    expand_query_by_intent,
)
from app.services.recommendation_service import (
    recommend_events,
    format_recommendations,
)
from app.services.retrieval_service import retriever
from app.services.support_service import answer_support_question
from app.services.risk_service import (
    evaluate_risk_context,
    should_block_transfer_like_action,
)


def clean_answer_text(text: str, lang: str = "zh") -> str:
    """
    从 FAQ / policy chunk 中按语言提取答案。
    优先级：
    1) A_ZH / A_EN
    2) 旧格式 A:
    3) 去掉所有 Q: 行后的普通文本 fallback
    """
    text = text.replace("\r", "\n").strip()

    def _normalize_answer(answer: str) -> str:
        answer = answer.strip()
        answer = re.sub(r"\n+", "\n", answer)
        answer = re.sub(r"[ \t]+", " ", answer)
        return answer.strip()

    if lang == "en":
        match = re.search(
            r"(?:^|\n)A_EN\s*:\s*(.+?)(?=\nA_ZH\s*:|\nA\s*:|\nQ\s*:|$)",
            text,
            flags=re.IGNORECASE | re.DOTALL,
        )
        if match:
            return _normalize_answer(match.group(1))

    if lang == "zh":
        match = re.search(
            r"(?:^|\n)A_ZH\s*:\s*(.+?)(?=\nA_EN\s*:|\nA\s*:|\nQ\s*:|$)",
            text,
            flags=re.IGNORECASE | re.DOTALL,
        )
        if match:
            return _normalize_answer(match.group(1))

    # fallback: 旧格式 A:
    answer_match = re.search(
        r"(?:^|\n)A\s*:\s*(.+)",
        text,
        flags=re.IGNORECASE | re.DOTALL,
    )
    if answer_match:
        return _normalize_answer(answer_match.group(1))

    # fallback: 去掉所有 Q 行 / A_ZH / A_EN 标记后返回
    lines = []
    for line in text.splitlines():
        stripped = line.strip()
        if re.match(r"^(Q|Question)\s*:", stripped, flags=re.IGNORECASE):
            continue
        stripped = re.sub(r"^(A_ZH|A_EN|A)\s*:\s*", "", stripped, flags=re.IGNORECASE)
        if stripped:
            lines.append(stripped)

    cleaned = "\n".join(lines).strip()
    cleaned = re.sub(r"\n+", "\n", cleaned)
    cleaned = re.sub(r"[ \t]+", " ", cleaned)
    return cleaned


def prepend_risk_banner(answer: str, risk_ctx: Dict[str, Any], lang: str) -> str:
    if risk_ctx.get("risk_level") not in ("medium", "high"):
        return answer

    banner = (
        "⚠️ 提示：系统检测到你的账号或设备存在一定风险，为保证账号和票务安全，部分操作可能需要额外验证或被限制。"
        if lang == "zh"
        else "⚠️ Note: Our system detected some risk signals related to your account or device. For your security, some actions may require additional verification or limitations."
    )

    user_message = risk_ctx.get("user_message")
    if user_message:
        return banner + "\n\n" + user_message + "\n\n" + answer
    return banner + "\n\n" + answer


def build_next_actions(intent: str, risk_ctx: Dict[str, Any], lang: str) -> List[str]:
    high_risk = risk_ctx.get("risk_level") == "high"

    if lang == "zh":
        if intent == "refund":
            return ["查看订单状态", "联系人工客服", "了解退款政策"]
        if intent == "transfer":
            return (
                ["查看转票规则", "联系人工客服", "提交申诉"]
                if high_risk
                else ["查看转票规则", "开始转票"]
            )
        if intent == "event_search":
            return ["查看推荐演出", "按城市筛选", "按类型筛选"]
        return ["查看 FAQ", "联系人工客服"]

    if intent == "refund":
        return ["Check order status", "Contact support", "View refund policy"]
    if intent == "transfer":
        return (
            ["View transfer rules", "Contact support", "Submit an appeal"]
            if high_risk
            else ["View transfer rules", "Start transfer"]
        )
    if intent == "event_search":
        return ["View recommended events", "Filter by city", "Filter by genre"]
    return ["View FAQ", "Contact support"]


def _build_risk_ctx(user_ctx: Dict[str, Any], lang: str) -> Dict[str, Any]:
    if user_ctx.get("_sb"):
        return evaluate_risk_context(
            sb=user_ctx.get("_sb"),
            payload=user_ctx,
            lang=lang,
        )

    risk = user_ctx.get("risk") or {}
    return {
        "risk_score": float(risk.get("risk_score") or 0.0),
        "risk_level": risk.get("risk_level") or "low",
        "risk_type": risk.get("risk_type") or "none",
        "reasons": risk.get("reasons") or [],
        "signals": risk.get("signals") or {},
        "recommended_action": risk.get("recommended_action") or "allow",
        "user_message": risk.get("user_message"),
    }


def _fallback_answer(lang: str) -> str:
    return (
        "抱歉，在当前知识库中没有找到与你的问题足够相关的信息。请查看 FAQ 页面或联系人工客服。"
        if lang == "zh"
        else "Sorry, I couldn't find information closely related to your question in the current knowledge base. Please check the FAQ or contact support."
    )


def _low_confidence_answer(lang: str) -> str:
    return (
        "抱歉，根据当前 FAQ/政策内容，我没有找到足够匹配的问题。请查看 FAQ 页面或联系人工客服获取更详细的说明。"
        if lang == "zh"
        else "Sorry, I couldn't find a confident match for your question in the current FAQ/policy data. Please check the FAQ page or contact support for more details."
    )


def _safe_clean_primary_answer(results: List[Dict[str, Any]], lang: str) -> str:
    if not results:
        return _fallback_answer(lang)

    primary = clean_answer_text(results[0]["text"], lang=lang)
    if primary:
        return primary

    return (
        "抱歉，我检索到了相关内容，但没能整理出清晰答案。请查看 FAQ 页面或联系人工客服。"
        if lang == "zh"
        else "I retrieved related content, but couldn't form a clear answer. Please check the FAQ or contact support."
    )


def answer_question(req: AskRequest) -> Dict[str, Any]:
    lang = detect_language(req.question)
    corrected = correct_spelling_en(req.question) if lang == "en" else req.question
    q_norm = normalize_question(corrected)

    user_ctx = req.context or {}
    intent = classify_intent(q_norm)
    risk_ctx = _build_risk_ctx(user_ctx, lang)

    # 1) 高风险转票直接拦截
    if intent == "transfer" and should_block_transfer_like_action(risk_ctx):
        answer = (
            "由于当前账号存在较高风险信号，转票相关操作暂时受到限制。若需继续处理，请联系人工客服或提交申诉。"
            if lang == "zh"
            else "Because the current account shows high-risk signals, ticket transfer-related actions are temporarily restricted. Please contact support or submit an appeal if you need further help."
        )
        return {
            "answer": answer,
            "citations": ["risk://transfer-blocked"],
            "scores": [risk_ctx["risk_score"]],
            "intent": intent,
            "lang": lang,
            "risk_level": risk_ctx["risk_level"],
            "risk_score": risk_ctx["risk_score"],
            "risk_type": risk_ctx["risk_type"],
            "risk_reasons": risk_ctx["reasons"],
            "recommended_action": risk_ctx["recommended_action"],
            "answer_mode": "risk_block",
            "next_actions": build_next_actions(intent, risk_ctx, lang),
        }

    # 2) 先走 support 问答（订单、退款状态等强结构化支持问题）
    support_result = answer_support_question(q_norm, user_ctx, lang)
    if support_result:
        core_answer = support_result["answer"]
        if risk_ctx["risk_level"] in ("medium", "high"):
            core_answer = prepend_risk_banner(core_answer, risk_ctx, lang)

        return {
            "answer": core_answer,
            "citations": [support_result["source"]],
            "scores": [support_result["score"]],
            "intent": intent,
            "lang": lang,
            "risk_level": risk_ctx["risk_level"],
            "risk_score": risk_ctx["risk_score"],
            "risk_type": risk_ctx["risk_type"],
            "risk_reasons": risk_ctx["reasons"],
            "recommended_action": risk_ctx["recommended_action"],
            "answer_mode": "support_answer",
            "next_actions": build_next_actions(intent, risk_ctx, lang),
        }

    # 3) 演出推荐分支
    if intent == "event_search":
        recs = recommend_events(q_norm, user_ctx)

        if risk_ctx["risk_level"] == "high":
            recs = recs[:3]
        elif risk_ctx["risk_level"] == "medium":
            recs = recs[:4]

        if not recs:
            answer = (
                "在当前数据集中，没有找到与你条件匹配的近期演出。你可以尝试更换城市、时间范围或音乐类型再试一次。"
                if lang == "zh"
                else "I couldn't find any upcoming events that match your query in the current dataset. Please try another city, date range, or genre."
            )
            if risk_ctx["risk_level"] in ("medium", "high"):
                answer = prepend_risk_banner(answer, risk_ctx, lang)

            return {
                "answer": answer,
                "citations": [],
                "scores": [],
                "intent": intent,
                "lang": lang,
                "risk_level": risk_ctx["risk_level"],
                "risk_score": risk_ctx["risk_score"],
                "risk_type": risk_ctx["risk_type"],
                "risk_reasons": risk_ctx["reasons"],
                "recommended_action": risk_ctx["recommended_action"],
                "answer_mode": "event_recommendation_empty",
                "next_actions": build_next_actions(intent, risk_ctx, lang),
            }

        answer = format_recommendations(recs, lang=lang)
        if risk_ctx["risk_level"] in ("medium", "high"):
            answer = prepend_risk_banner(answer, risk_ctx, lang)

        return {
            "answer": answer,
            "citations": [f"event://{r['event_id']}" for r in recs],
            "scores": [r["score"] for r in recs],
            "intent": intent,
            "lang": lang,
            "risk_level": risk_ctx["risk_level"],
            "risk_score": risk_ctx["risk_score"],
            "risk_type": risk_ctx["risk_type"],
            "risk_reasons": risk_ctx["reasons"],
            "recommended_action": risk_ctx["recommended_action"],
            "answer_mode": "event_recommendation",
            "next_actions": build_next_actions(intent, risk_ctx, lang),
        }

    # 4) FAQ / policy 普通检索分支
    search_query = expand_query_by_intent(intent, q_norm, lang=lang)
    alpha = 0.5 if lang == "zh" else 0.6

    # 4.1 先只查 FAQ / policy
    results = retriever.search(
        search_query,
        top_k=5,
        alpha=alpha,
        source_prefixes=["doc://faq#", "doc://policy#"],
        min_score=0.0,
    )

    # 4.2 FAQ / policy 没结果，再回退全库
    if not results:
        results = retriever.search(
            search_query,
            top_k=5,
            alpha=alpha,
            source_prefixes=None,
            min_score=0.0,
        )

    if not results:
        core_answer = _fallback_answer(lang)
        if risk_ctx["risk_level"] in ("medium", "high"):
            core_answer = prepend_risk_banner(core_answer, risk_ctx, lang)

        return {
            "answer": core_answer,
            "citations": [],
            "scores": [],
            "intent": intent,
            "lang": lang,
            "risk_level": risk_ctx["risk_level"],
            "risk_score": risk_ctx["risk_score"],
            "risk_type": risk_ctx["risk_type"],
            "risk_reasons": risk_ctx["reasons"],
            "recommended_action": risk_ctx["recommended_action"],
            "answer_mode": "kb_no_result",
            "next_actions": build_next_actions(intent, risk_ctx, lang),
        }

    best_score = float(results[0]["score"])
    threshold = 0.04 if lang == "zh" else 0.05

    if best_score < threshold:
        core_answer = _low_confidence_answer(lang)
        if risk_ctx["risk_level"] in ("medium", "high"):
            core_answer = prepend_risk_banner(core_answer, risk_ctx, lang)

        return {
            "answer": core_answer,
            "citations": [c["source"] for c in results],
            "scores": [c["score"] for c in results],
            "intent": intent,
            "lang": lang,
            "risk_level": risk_ctx["risk_level"],
            "risk_score": risk_ctx["risk_score"],
            "risk_type": risk_ctx["risk_type"],
            "risk_reasons": risk_ctx["reasons"],
            "recommended_action": risk_ctx["recommended_action"],
            "answer_mode": "kb_low_confidence",
            "next_actions": build_next_actions(intent, risk_ctx, lang),
        }

    core_answer = _safe_clean_primary_answer(results, lang)
    if risk_ctx["risk_level"] in ("medium", "high"):
        core_answer = prepend_risk_banner(core_answer, risk_ctx, lang)

    return {
        "answer": core_answer,
        "citations": [c["source"] for c in results],
        "scores": [c["score"] for c in results],
        "intent": intent,
        "lang": lang,
        "risk_level": risk_ctx["risk_level"],
        "risk_score": risk_ctx["risk_score"],
        "risk_type": risk_ctx["risk_type"],
        "risk_reasons": risk_ctx["reasons"],
        "recommended_action": risk_ctx["recommended_action"],
        "answer_mode": "kb_answer",
        "next_actions": build_next_actions(intent, risk_ctx, lang),
    }