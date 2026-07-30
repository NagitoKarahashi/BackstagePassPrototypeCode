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
from app.services.chatbot_events_service import (
    build_purchase_action,
    event_to_assistant_card,
    extract_ticket_quantity,
    find_chatbot_events,
    format_artist_overview,
    format_event_details,
    format_live_recommendations,
    is_artist_info_request,
    is_event_detail_request,
    is_generic_event_search,
    is_purchase_request,
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
        if intent == "artist_info":
            return ["打开艺人页", "查看该艺人的活动", "购买门票"]
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
    if intent == "artist_info":
        return ["Open artist page", "View artist events", "Buy tickets"]
    if intent == "event_search":
        return ["View recommended events", "Filter by city", "Filter by genre"]
    return ["View FAQ", "Contact support"]


def _build_risk_ctx(
    user_ctx: Dict[str, Any],
    lang: str,
    sb: Any = None,
) -> Dict[str, Any]:
    if sb is not None:
        return evaluate_risk_context(
            sb=sb,
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


def answer_question(req: AskRequest, sb: Any) -> Dict[str, Any]:
    lang = detect_language(req.question)

    # Keep the original wording for catalogue, artist and purchase matching.
    # TextBlob-style spelling correction can corrupt proper nouns such as
    # "Luna Echo", "Hong Kong" and "Post Malone". Conservative correction is
    # therefore applied only later, inside the FAQ/policy retrieval branch.
    q_norm = normalize_question(req.question)

    user_ctx = req.context or {}
    intent = classify_intent(q_norm)
    risk_ctx = _build_risk_ctx(user_ctx, lang, sb=sb)

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

    # 2) 购票请求先返回确认动作，不在自然语言请求阶段写数据库
    if is_purchase_request(q_norm):
        quantity = extract_ticket_quantity(q_norm)
        events = find_chatbot_events(
            sb,
            q_norm,
            user_ctx,
            only_available=True,
            allow_upcoming_fallback=is_generic_event_search(q_norm),
            limit=5,
        )

        if not events:
            answer = (
                "没有找到与你的购票请求匹配、且当前仍可购买的活动。请告诉我活动名称、艺人或城市。"
                if lang == "zh"
                else "I couldn't find an on-sale event matching your purchase request. Please provide an event title, artist, or city."
            )
            if risk_ctx["risk_level"] in ("medium", "high"):
                answer = prepend_risk_banner(answer, risk_ctx, lang)

            return {
                "answer": answer,
                "citations": [],
                "scores": [],
                "intent": "purchase",
                "lang": lang,
                "risk_level": risk_ctx["risk_level"],
                "risk_score": risk_ctx["risk_score"],
                "risk_type": risk_ctx["risk_type"],
                "risk_reasons": risk_ctx["reasons"],
                "recommended_action": risk_ctx["recommended_action"],
                "answer_mode": "purchase_event_not_found",
                "events": [],
                "action": None,
                "next_actions": (
                    ["查看近期活动", "按城市筛选"]
                    if lang == "zh"
                    else ["View upcoming events", "Filter by city"]
                ),
            }

        action = build_purchase_action(events, quantity, lang)
        cards = [event_to_assistant_card(event) for event in events]
        if len(events) == 1:
            answer = (
                f"我找到了 {events[0].get('title') or '这场活动'}。请核对下方活动和 {quantity} 张票的模拟订单，再点击确认。"
                if lang == "zh"
                else f"I found {events[0].get('title') or 'the event'}. Review the event and the mock order for {quantity} ticket(s), then confirm."
            )
        else:
            answer = (
                f"我找到了几场可能相关的活动。请选择一场，再确认购买 {quantity} 张票。"
                if lang == "zh"
                else f"I found several possible events. Choose one, then confirm the mock purchase for {quantity} ticket(s)."
            )

        if risk_ctx["risk_level"] in ("medium", "high"):
            answer = prepend_risk_banner(answer, risk_ctx, lang)

        return {
            "answer": answer,
            "citations": [f"event://{event.get('id')}" for event in events],
            "scores": [1.0 for _ in events],
            "intent": "purchase",
            "lang": lang,
            "risk_level": risk_ctx["risk_level"],
            "risk_score": risk_ctx["risk_score"],
            "risk_type": risk_ctx["risk_type"],
            "risk_reasons": risk_ctx["reasons"],
            "recommended_action": risk_ctx["recommended_action"],
            "answer_mode": action["type"],
            "events": cards,
            "action": action,
            "next_actions": (
                ["确认模拟购票", "选择其他活动"]
                if lang == "zh"
                else ["Confirm mock purchase", "Choose another event"]
            ),
        }

    # 3) 艺人介绍：基于 Supabase 当前活动资料生成，不虚构外部履历
    if intent == "artist_info" or is_artist_info_request(q_norm):
        events = find_chatbot_events(
            sb,
            q_norm,
            user_ctx,
            only_available=False,
            allow_upcoming_fallback=False,
            include_past=True,
            limit=8,
        )
        if events:
            answer = format_artist_overview(events, lang)
            if risk_ctx["risk_level"] in ("medium", "high"):
                answer = prepend_risk_banner(answer, risk_ctx, lang)
            return {
                "answer": answer,
                "citations": [f"event://{event.get('id')}" for event in events],
                "scores": [1.0 for _ in events],
                "intent": "artist_info",
                "lang": lang,
                "risk_level": risk_ctx["risk_level"],
                "risk_score": risk_ctx["risk_score"],
                "risk_type": risk_ctx["risk_type"],
                "risk_reasons": risk_ctx["reasons"],
                "recommended_action": risk_ctx["recommended_action"],
                "answer_mode": "artist_overview",
                "events": [event_to_assistant_card(event) for event in events],
                "action": None,
                "next_actions": build_next_actions("artist_info", risk_ctx, lang),
            }

        answer = (
            "当前活动数据库中没有找到对应艺人的资料。请提供艺人名称，或先打开一场相关活动再询问。"
            if lang == "zh"
            else "I couldn't find that artist in the current event catalogue. Provide the artist name, or open a related event and ask again."
        )
        return {
            "answer": answer,
            "citations": [],
            "scores": [],
            "intent": "artist_info",
            "lang": lang,
            "risk_level": risk_ctx["risk_level"],
            "risk_score": risk_ctx["risk_score"],
            "risk_type": risk_ctx["risk_type"],
            "risk_reasons": risk_ctx["reasons"],
            "recommended_action": risk_ctx["recommended_action"],
            "answer_mode": "artist_not_found",
            "events": [],
            "action": None,
            "next_actions": build_next_actions("artist_info", risk_ctx, lang),
        }

    # 4) 当前活动详情：优先读取 Supabase 中的真实活动记录
    has_current_event = bool(
        user_ctx.get("selected_event_id") or user_ctx.get("current_event_id")
    )
    if is_event_detail_request(q_norm) or (
        has_current_event and intent in {"price", "venue_info"}
    ):
        events = find_chatbot_events(
            sb,
            q_norm,
            user_ctx,
            only_available=False,
            allow_upcoming_fallback=False,
            include_past=True,
            limit=3,
        )
        if events:
            answer = format_event_details(events, lang)
            if risk_ctx["risk_level"] in ("medium", "high"):
                answer = prepend_risk_banner(answer, risk_ctx, lang)
            return {
                "answer": answer,
                "citations": [f"event://{event.get('id')}" for event in events],
                "scores": [1.0 for _ in events],
                "intent": intent,
                "lang": lang,
                "risk_level": risk_ctx["risk_level"],
                "risk_score": risk_ctx["risk_score"],
                "risk_type": risk_ctx["risk_type"],
                "risk_reasons": risk_ctx["reasons"],
                "recommended_action": risk_ctx["recommended_action"],
                "answer_mode": "event_details",
                "events": [event_to_assistant_card(event) for event in events],
                "action": None,
                "next_actions": (
                    ["购买门票", "查看其他活动"]
                    if lang == "zh"
                    else ["Buy tickets", "View other events"]
                ),
            }

    # 5) 演出推荐分支改为读取 Supabase，不再读取 events.csv
    if intent == "event_search":
        event_limit = 3 if risk_ctx["risk_level"] == "high" else 4 if risk_ctx["risk_level"] == "medium" else 5
        events = find_chatbot_events(
            sb,
            q_norm,
            user_ctx,
            only_available=True,
            allow_upcoming_fallback=is_generic_event_search(q_norm),
            limit=event_limit,
        )

        if not events:
            answer = (
                "当前活动数据库中没有找到与你条件匹配、且仍可购票的近期活动。你可以尝试更换城市、艺人或音乐类型。"
                if lang == "zh"
                else "I couldn't find an upcoming on-sale event matching your query in the current catalogue. Try another city, artist, or genre."
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
                "events": [],
                "action": None,
                "next_actions": build_next_actions(intent, risk_ctx, lang),
            }

        answer = format_live_recommendations(events, lang=lang)
        if risk_ctx["risk_level"] in ("medium", "high"):
            answer = prepend_risk_banner(answer, risk_ctx, lang)

        return {
            "answer": answer,
            "citations": [f"event://{event.get('id')}" for event in events],
            "scores": [1.0 for _ in events],
            "intent": intent,
            "lang": lang,
            "risk_level": risk_ctx["risk_level"],
            "risk_score": risk_ctx["risk_score"],
            "risk_type": risk_ctx["risk_type"],
            "risk_reasons": risk_ctx["reasons"],
            "recommended_action": risk_ctx["recommended_action"],
            "answer_mode": "event_recommendation",
            "events": [event_to_assistant_card(event) for event in events],
            "action": None,
            "next_actions": build_next_actions(intent, risk_ctx, lang),
        }

    # 6) 结构化支持问题（订单、退款状态等）
    support_result = answer_support_question(q_norm, user_ctx, lang)
    if support_result:
        answer = support_result["answer"]
        if risk_ctx["risk_level"] in ("medium", "high"):
            answer = prepend_risk_banner(answer, risk_ctx, lang)

        return {
            "answer": answer,
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

    # 7) FAQ / policy 普通检索分支
    # English spelling correction remains useful for policy questions, but it
    # must not run before event/artist matching because proper nouns are easily
    # rewritten into unrelated common words.
    faq_question = (
        normalize_question(correct_spelling_en(req.question))
        if lang == "en"
        else q_norm
    )
    search_query = expand_query_by_intent(intent, faq_question, lang=lang)
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
