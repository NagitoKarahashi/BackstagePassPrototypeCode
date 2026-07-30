import logging
import re
import unicodedata
from difflib import SequenceMatcher
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import HTTPException

from app.services.events_service import EVENT_SELECT, get_event_by_id_service


MAX_CHATBOT_TICKET_QUANTITY = 6
logger = logging.getLogger(__name__)

_PURCHASE_WORDS = {
    "buy",
    "book",
    "booking",
    "purchase",
    "ticket",
    "tickets",
    "order",
    "pay",
    "买",
    "购买",
    "购票",
    "买票",
    "订票",
    "预订",
    "门票",
    "票",
    "下单",
    "支付",
}

_EVENT_STOP_WORDS = _PURCHASE_WORDS | {
    "a",
    "an",
    "and",
    "about",
    "any",
    "can",
    "could",
    "event",
    "events",
    "for",
    "give",
    "help",
    "i",
    "in",
    "information",
    "introduce",
    "me",
    "of",
    "on",
    "please",
    "show",
    "tell",
    "the",
    "this",
    "to",
    "want",
    "what",
    "available",
    "find",
    "latest",
    "list",
    "near",
    "nearby",
    "recent",
    "recommend",
    "recommendation",
    "recommendations",
    "some",
    "upcoming",
    "活动",
    "演出",
    "这场",
    "这个",
    "介绍",
    "一下",
    "帮我",
    "我要",
    "想要",
    "可以",
    "吗",
    "张",
    "当前",
    "查看",
    "近期",
    "最近",
    "有什么",
    "可购票",
    "推荐",
    "列出",
    "一些",
    "给我看看",
    "看看",
    "找一下",
}

_CURRENT_EVENT_REFERENCES = [
    "this event",
    "this show",
    "this concert",
    "current event",
    "这个活动",
    "这个演出",
    "这场活动",
    "这场演出",
    "这场",
    "它",
]

_CHINESE_QUANTITIES = {
    "一": 1,
    "两": 2,
    "二": 2,
    "三": 3,
    "四": 4,
    "五": 5,
    "六": 6,
}

_ENGLISH_QUANTITIES = {
    "one": 1,
    "two": 2,
    "three": 3,
    "four": 4,
    "five": 5,
    "six": 6,
}

_ARTIST_INFO_WORDS = {
    "about this artist",
    "artist profile",
    "introduce the artist",
    "tell me about the artist",
    "who is the artist",
    "介绍一下这个艺人",
    "介绍一下艺人",
    "介绍艺人",
    "介绍歌手",
    "了解这个艺人",
    "艺人是谁",
    "歌手是谁",
}


_TEXT_ALIASES = {
    # City aliases and common Chinese query forms. These values deliberately
    # normalise to the wording used by the current events table.
    "hongkong": "hong kong",
    "h.k.": "hong kong",
    "香港": "hong kong",
    "东京": "tokyo",
    "東京": "tokyo",
    "大阪": "osaka",
    "新加坡": "singapore",
    "马尼拉": "manila",
    "馬尼拉": "manila",
    # Genre aliases used by catalogue questions.
    "流行音乐": "pop",
    "流行音樂": "pop",
    "流行": "pop",
    "摇滚": "rock",
    "搖滾": "rock",
    "电子音乐": "electronic",
    "電子音樂": "electronic",
    "电子": "electronic",
    "電子": "electronic",
    "独立音乐": "indie",
    "獨立音樂": "indie",
    "独立": "indie",
    "獨立": "indie",
    "爵士": "jazz",
}


_EVENT_DETAIL_WORDS = {
    "about",
    "artist",
    "date",
    "describe",
    "description",
    "detail",
    "details",
    "information",
    "introduce",
    "location",
    "price",
    "start",
    "time",
    "venue",
    "when",
    "where",
    "who",
    "介绍",
    "信息",
    "内容",
    "多少钱",
    "时间",
    "活动详情",
    "演出详情",
    "票价",
    "艺人",
    "详情",
    "地点",
    "场馆",
}


def is_purchase_request(text: str) -> bool:
    """Return True only for an action request, not every mention of a ticket."""
    lowered = text.lower()
    if re.search(
        r"\b(?:buy|book|purchase|order|pay\s+for)\b.{0,40}"
        r"\b(?:ticket|tickets|event|show|concert)\b",
        lowered,
    ):
        return True
    if re.search(r"\b(?:want|need)\b.{0,20}\b(?:ticket|tickets)\b", lowered):
        return True
    return bool(
        re.search(
            r"(?:买|购买|购票|买票|订票|预订|下单|支付).{0,12}(?:票|门票|活动|演出)",
            text,
        )
    )


def is_generic_event_search(text: str) -> bool:
    """Generic catalogue requests may fall back to the next available events."""
    return not _query_tokens(text)


def is_artist_info_request(text: str) -> bool:
    lowered = text.lower().strip()
    if any(word in lowered for word in _ARTIST_INFO_WORDS):
        return True
    if re.search(r"\b(?:introduce|describe)\s+(?!this\s+(?:event|show|concert))[^?]{2,80}$", lowered):
        return True
    if re.search(r"\btell\s+me\s+about\s+(?!this\s+(?:event|show|concert))[^?]{2,80}$", lowered):
        return True
    if re.search(
        r"(?:介绍一下|介绍|了解一下).{1,30}(?:艺人|歌手|乐队|组合)$",
        text,
    ):
        return True
    return bool(
        re.search(
            r"(?:介绍一下|介绍|了解一下)(?!.*(?:这个活动|这场活动|这个演出|这场演出|音乐会|演唱会)).{2,50}$",
            text,
        )
    )


def is_event_detail_request(text: str) -> bool:
    lowered = text.lower()
    return any(word in lowered for word in _EVENT_DETAIL_WORDS)


def extract_ticket_quantity(text: str, default: int = 1) -> int:
    """Extract a small ticket quantity without mistaking years or prices for quantity."""
    patterns = [
        r"(\d+)\s*(?:张|份|位|个)\s*(?:票|门票)?",
        r"(?:buy|book|purchase|want|need)\s+(\d+)\s+(?:ticket|tickets)",
        r"(\d+)\s+(?:ticket|tickets)",
    ]
    for pattern in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            return max(1, min(int(match.group(1)), MAX_CHATBOT_TICKET_QUANTITY))

    match = re.search(r"([一两二三四五六])\s*张", text)
    if match:
        return _CHINESE_QUANTITIES[match.group(1)]

    match = re.search(
        r"\b(one|two|three|four|five|six)\s+(?:ticket|tickets)\b",
        text,
        flags=re.IGNORECASE,
    )
    if match:
        return _ENGLISH_QUANTITIES[match.group(1).lower()]

    return max(1, min(default, MAX_CHATBOT_TICKET_QUANTITY))


def _normalise_text(value: Any) -> str:
    text = unicodedata.normalize("NFKC", str(value or "")).strip().lower()
    text = (
        text.replace("’", "'")
        .replace("‘", "'")
        .replace("–", "-")
        .replace("—", "-")
    )
    for source, target in _TEXT_ALIASES.items():
        text = text.replace(source, f" {target} ")
    return re.sub(r"\s+", " ", text).strip()


def _query_tokens(text: str) -> set[str]:
    cleaned = _normalise_text(text)
    # Possessives should not turn an artist token into a different word:
    # "Post Malone's" -> "Post Malone".
    cleaned = re.sub(r"\b([a-z0-9][a-z0-9&'-]*)'s\b", r"\1", cleaned)
    # Chinese has no spaces, so remove known intent phrases before tokenisation.
    # This lets "我要买两张票" resolve to the event currently open on screen,
    # while "我要买香港活动的票" keeps "香港" as an event-search token.
    chinese_stop_words = [
        word for word in _EVENT_STOP_WORDS if re.search(r"[\u4e00-\u9fff]", word)
    ]
    for stop_word in sorted(chinese_stop_words, key=len, reverse=True):
        cleaned = cleaned.replace(stop_word, " ")

    tokens = set(re.findall(r"[a-z0-9][a-z0-9&'-]+|[\u4e00-\u9fff]{2,}", cleaned))
    return {token for token in tokens if token not in _EVENT_STOP_WORDS and not token.isdigit()}


def _event_start(event: Dict[str, Any]) -> Optional[str]:
    value = event.get("starts_at") or event.get("start_time")
    return str(value) if value else None


def _parse_event_start(event: Dict[str, Any]) -> Optional[datetime]:
    raw_value = _event_start(event)
    if not raw_value:
        return None

    try:
        parsed = datetime.fromisoformat(raw_value.replace("Z", "+00:00"))
    except (TypeError, ValueError):
        return None

    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def event_to_assistant_card(event: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "id": str(event.get("id") or ""),
        "event_code": event.get("event_code"),
        "title": event.get("title") or "Untitled event",
        "artist": event.get("artist"),
        "genre": event.get("genre"),
        "city": event.get("city"),
        "country": event.get("country"),
        "venue_name": event.get("venue_name"),
        "description": event.get("description"),
        "price": event.get("price"),
        "stock_left": event.get("stock_left"),
        "start_time": _event_start(event),
        "poster_url": event.get("poster_url") or event.get("cover_url"),
        "status": event.get("status"),
    }


def _is_current_event_reference(question: str) -> bool:
    q = question.lower()
    return any(reference in q for reference in _CURRENT_EVENT_REFERENCES)


def _filter_explicit_catalogue_fields(
    question: str,
    events: List[Dict[str, Any]],
) -> tuple[List[Dict[str, Any]], set[str]]:
    """Apply exact artist/location/genre constraints stated in the query.

    This prevents a location-only request such as "events in Hong Kong" from
    being re-ranked by incidental title/description matches. The remaining token
    set is used to decide whether free-text scoring is still needed.
    """
    normalised_question = _normalise_text(question)
    remaining_tokens = set(_query_tokens(normalised_question))
    filtered = list(events)

    # Artist and location values are matched as full normalised phrases.
    for fields in (("artist",), ("city", "country")):
        matched_values: set[str] = set()
        for event in filtered:
            for field in fields:
                value = _normalise_text(event.get(field))
                if len(value) >= 2 and value in normalised_question:
                    matched_values.add(value)

        if not matched_values:
            continue

        subset = [
            event
            for event in filtered
            if any(
                _normalise_text(event.get(field)) in matched_values
                for field in fields
                if _normalise_text(event.get(field))
            )
        ]
        if subset:
            filtered = subset
            for value in matched_values:
                remaining_tokens.difference_update(_query_tokens(value))

    # Genre values are often compound strings (for example "J-Pop / Rock"),
    # so exact query tokens are a better constraint than full-phrase matching.
    genre_tokens = set()
    for event in filtered:
        genre_tokens.update(_query_tokens(event.get("genre") or ""))
    requested_genres = remaining_tokens & genre_tokens
    if requested_genres:
        subset = [
            event
            for event in filtered
            if requested_genres & _query_tokens(event.get("genre") or "")
        ]
        if subset:
            filtered = subset
            remaining_tokens.difference_update(requested_genres)

    return filtered, remaining_tokens


def _score_event(question: str, event: Dict[str, Any]) -> float:
    q = _normalise_text(question)
    tokens = _query_tokens(q)
    score = 0.0

    weighted_fields = [
        ("title", 8.0),
        ("artist", 5.0),
        ("venue_name", 3.0),
        ("city", 2.5),
        ("country", 1.5),
        ("genre", 2.5),
        ("event_code", 7.0),
        ("description", 0.75),
    ]

    for field, weight in weighted_fields:
        value = _normalise_text(event.get(field))
        if not value:
            continue

        if len(value) >= 3 and value in q:
            score += weight

        field_tokens = _query_tokens(value)
        if tokens and field_tokens:
            overlap_tokens = tokens & field_tokens
            score += len(overlap_tokens) * min(weight, 2.0)

            # Conservative typo tolerance for names such as "Malone/Melone".
            # Exact matches still dominate; fuzzy credit is only awarded to
            # reasonably long, unmatched tokens with a high similarity ratio.
            unmatched_query = [token for token in tokens - overlap_tokens if len(token) >= 4]
            unmatched_field = [token for token in field_tokens - overlap_tokens if len(token) >= 4]
            for query_token in unmatched_query:
                best_ratio = max(
                    (SequenceMatcher(None, query_token, field_token).ratio() for field_token in unmatched_field),
                    default=0.0,
                )
                if best_ratio >= 0.84:
                    score += best_ratio * min(weight, 1.25)

        # Chinese titles and artist names are often not separated into tokens.
        for token in tokens:
            if (
                re.search(r"[\u4e00-\u9fff]", token)
                and (token in value or value in token)
            ):
                score += min(weight, 2.0)

    return score


def _catalogue_date_sort_key(event: Dict[str, Any]) -> tuple[int, float]:
    """Upcoming first/soonest; then past most-recent; undated last."""
    parsed = _parse_event_start(event)
    if parsed is None:
        return (2, float("inf"))

    now = datetime.now(timezone.utc)
    timestamp = parsed.timestamp()
    if parsed >= now:
        return (0, timestamp)
    return (1, -timestamp)


def _list_catalogue_events(
    sb,
    only_available: bool,
    *,
    include_past: bool = False,
    limit: int = 100,
) -> List[Dict[str, Any]]:
    """Load published catalogue rows and apply date rules in Python.

    The database contains both ``starts_at`` and legacy ``start_time`` values.
    Filtering only ``starts_at`` in PostgREST would drop valid legacy rows.
    Artist/profile queries may include historical records, while discovery and
    purchasing remain restricted to upcoming events.
    """
    query = sb.table("events").select(EVENT_SELECT).eq("status", "published")
    if only_available:
        query = query.gt("stock_left", 0)

    response = query.limit(max(limit * 3, 100)).execute()
    rows = list(response.data or [])
    now = datetime.now(timezone.utc)

    if not include_past:
        rows = [
            event
            for event in rows
            if (_parse_event_start(event) or datetime.min.replace(tzinfo=timezone.utc)) >= now
        ]

    rows.sort(key=_catalogue_date_sort_key)
    return rows[:limit]


def find_chatbot_events(
    sb,
    question: str,
    context: Optional[Dict[str, Any]] = None,
    *,
    only_available: bool = False,
    allow_upcoming_fallback: bool = False,
    include_past: bool = False,
    limit: int = 5,
) -> List[Dict[str, Any]]:
    """
    Resolve an event from the current page first, then search the live Supabase catalogue.
    It intentionally returns structured rows so the frontend can render event cards.
    """
    context = context or {}
    current_event_id = context.get("selected_event_id") or context.get("current_event_id")

    if current_event_id and (
        _is_current_event_reference(question)
        or is_event_detail_request(question)
        or not _query_tokens(question)
        or context.get("selected_event_id")
    ):
        try:
            current = get_event_by_id_service(sb, str(current_event_id))
            start = _parse_event_start(current)
            is_on_sale = (
                current.get("status") == "published"
                and int(current.get("stock_left") or 0) > 0
                and (start is None or start >= datetime.now(timezone.utc))
            )
            if not only_available or is_on_sale:
                return [current]
        except Exception:
            pass

    try:
        events = _list_catalogue_events(
            sb,
            only_available=only_available,
            include_past=include_past,
        )
    except Exception:
        logger.exception("Unable to load upcoming events from Supabase for the chatbot")
        return []

    events, remaining_tokens = _filter_explicit_catalogue_fields(question, events)

    # If the query was fully explained by exact structured fields (for example
    # only a city or artist name), preserve catalogue date ordering instead of
    # letting repeated words in titles/descriptions distort the result order.
    if events and not remaining_tokens and _query_tokens(question):
        return events[:limit]

    scored = [(_score_event(question, event), event) for event in events]
    matched = [(score, event) for score, event in scored if score > 0]
    matched.sort(
        key=lambda item: (-item[0],) + _catalogue_date_sort_key(item[1])
    )

    if matched:
        return [event for _, event in matched[:limit]]

    return events[:limit] if allow_upcoming_fallback else []


def format_event_details(events: List[Dict[str, Any]], lang: str) -> str:
    if not events:
        return ""

    if len(events) > 1:
        intro = (
            "我找到了几场可能相关的活动。你可以查看下面的活动卡片："
            if lang == "zh"
            else "I found several possibly relevant events. You can review the event cards below:"
        )
    else:
        intro = (
            "这是我从当前活动资料中读取到的信息："
            if lang == "zh"
            else "Here is the information I found in the current event record:"
        )

    blocks = [intro]
    for event in events:
        title = event.get("title") or "Untitled event"
        artist = event.get("artist") or ("待公布" if lang == "zh" else "TBA")
        venue = event.get("venue_name") or event.get("city") or ("待公布" if lang == "zh" else "TBA")
        start_time = _event_start(event) or ("待公布" if lang == "zh" else "TBA")
        price = event.get("price")
        description = event.get("description") or (
            "暂无更多活动介绍。" if lang == "zh" else "No additional description is available."
        )

        if lang == "zh":
            price_text = f"{price}" if price is not None else "待公布"
            blocks.append(
                f"🎵 {title}\n"
                f"艺人：{artist}\n"
                f"时间：{start_time}\n"
                f"地点：{venue}\n"
                f"票价：{price_text}\n"
                f"{description}"
            )
        else:
            price_text = f"{price}" if price is not None else "TBA"
            blocks.append(
                f"🎵 {title}\n"
                f"Artist: {artist}\n"
                f"Date: {start_time}\n"
                f"Venue: {venue}\n"
                f"Price: {price_text}\n"
                f"{description}"
            )

    return "\n\n".join(blocks)


def format_artist_overview(events: List[Dict[str, Any]], lang: str) -> str:
    """Build an honest artist summary from current and historical event rows."""
    if not events:
        return ""

    artist_name = str(events[0].get("artist") or "").strip()
    related = [
        event
        for event in events
        if str(event.get("artist") or "").strip().lower() == artist_name.lower()
    ]
    if not related:
        related = events[:1]

    related.sort(key=_catalogue_date_sort_key)
    now = datetime.now(timezone.utc)
    upcoming = [
        event for event in related
        if (_parse_event_start(event) or datetime.min.replace(tzinfo=timezone.utc)) >= now
    ]
    past = [
        event for event in related
        if (_parse_event_start(event) is not None and _parse_event_start(event) < now)
    ]
    past.sort(
        key=lambda event: _parse_event_start(event)
        or datetime.min.replace(tzinfo=timezone.utc),
        reverse=True,
    )

    display_name = artist_name or ("待公布艺人" if lang == "zh" else "Artist TBA")
    genres = sorted({str(event.get("genre")).strip() for event in related if event.get("genre")})
    cities = sorted({str(event.get("city")).strip() for event in related if event.get("city")})
    descriptions = [
        str(event.get("description")).strip()
        for event in related
        if event.get("description")
    ]

    if lang == "zh":
        lines = [
            f"🎤 {display_name}",
            "以下介绍来自当前平台活动资料，而不是外部艺人百科。",
        ]
        if genres:
            lines.append(f"相关类型：{'、'.join(genres)}")
        if cities:
            lines.append(f"平台收录城市：{'、'.join(cities)}")
        lines.append(f"平台共收录相关活动：{len(related)} 场")
        if descriptions:
            lines.append(f"活动资料简介：{descriptions[0]}")

        if upcoming:
            next_event = upcoming[0]
            next_place = " · ".join(
                str(value) for value in [next_event.get("venue_name"), next_event.get("city")] if value
            ) or "待公布"
            lines.append(f"当前可查看的未来活动：{len(upcoming)} 场")
            lines.append(
                f"下一场：{next_event.get('title') or '未命名活动'}｜"
                f"{_event_start(next_event) or '待公布'}｜{next_place}"
            )
            lines.append("你可以打开艺人页查看全部活动，或选择未来活动继续购票。")
        elif past:
            recent = past[0]
            recent_place = " · ".join(
                str(value) for value in [recent.get("venue_name"), recent.get("city")] if value
            ) or "待公布"
            lines.append("当前目录中暂时没有该艺人的未来活动。")
            lines.append(
                f"最近收录活动：{recent.get('title') or '未命名活动'}｜"
                f"{_event_start(recent) or '待公布'}｜{recent_place}"
            )
            lines.append("你仍可打开艺人页查看已收录资料，但过期活动不能购票。")
        return "\n".join(lines)

    lines = [
        f"🎤 {display_name}",
        "This overview is derived from the platform's event catalogue rather than an external artist biography source.",
    ]
    if genres:
        lines.append(f"Related genres: {', '.join(genres)}")
    if cities:
        lines.append(f"Catalogue cities: {', '.join(cities)}")
    lines.append(f"Related events in the catalogue: {len(related)}")
    if descriptions:
        lines.append(f"Event-profile description: {descriptions[0]}")

    if upcoming:
        next_event = upcoming[0]
        next_place = " · ".join(
            str(value) for value in [next_event.get("venue_name"), next_event.get("city")] if value
        ) or "TBA"
        lines.append(f"Upcoming events currently listed: {len(upcoming)}")
        lines.append(
            f"Next event: {next_event.get('title') or 'Untitled event'} | "
            f"{_event_start(next_event) or 'TBA'} | {next_place}"
        )
        lines.append("Open the artist page for all listed events, or choose an upcoming event to continue to ticketing.")
    elif past:
        recent = past[0]
        recent_place = " · ".join(
            str(value) for value in [recent.get("venue_name"), recent.get("city")] if value
        ) or "TBA"
        lines.append("There is currently no upcoming event for this artist in the catalogue.")
        lines.append(
            f"Most recently listed event: {recent.get('title') or 'Untitled event'} | "
            f"{_event_start(recent) or 'TBA'} | {recent_place}"
        )
        lines.append("You can still open the artist page to review the listed record, but expired events cannot be purchased.")
    return "\n".join(lines)


def format_live_recommendations(events: List[Dict[str, Any]], lang: str) -> str:
    if not events:
        return ""
    intro = (
        "我从当前活动数据库中找到了这些仍可购票的近期活动："
        if lang == "zh"
        else "I found these upcoming events with tickets available in the current catalogue:"
    )
    lines = [intro]
    for event in events:
        title = event.get("title") or "Untitled event"
        artist = event.get("artist") or ("待公布" if lang == "zh" else "TBA")
        location = " · ".join(
            str(value) for value in [event.get("venue_name"), event.get("city")] if value
        )
        when = _event_start(event) or ("待公布" if lang == "zh" else "TBA")
        lines.append(f"• {title} — {artist} — {location or 'TBA'} — {when}")
    return "\n".join(lines)


def build_purchase_action(
    events: List[Dict[str, Any]],
    quantity: int,
    lang: str,
) -> Dict[str, Any]:
    cards = [event_to_assistant_card(event) for event in events]
    if len(cards) == 1:
        event = cards[0]
        return {
            "type": "purchase_confirmation",
            "requires_confirmation": True,
            "event_id": event["id"],
            "event_title": event["title"],
            "quantity": quantity,
            "unit_price": event.get("price"),
            "estimated_total": (
                float(event["price"]) * quantity
                if event.get("price") is not None
                else None
            ),
            "payment_mode": "mock",
            "label": "确认模拟购票" if lang == "zh" else "Confirm mock purchase",
        }

    return {
        "type": "purchase_selection",
        "requires_confirmation": True,
        "quantity": quantity,
        "event_ids": [event["id"] for event in cards],
        "payment_mode": "mock",
        "label": "选择活动" if lang == "zh" else "Choose an event",
    }


def confirm_chatbot_purchase(
    sb,
    external_auth_id: str,
    event_id: str,
    quantity: int,
    lang: str = "en",
) -> Dict[str, Any]:
    # Imported here to keep read-only event search independent from profile/order dependencies.
    from app.services.orders_service import create_order_service, pay_order_service

    quantity = max(1, min(quantity, MAX_CHATBOT_TICKET_QUANTITY))
    event = get_event_by_id_service(sb, event_id)

    if event.get("status") != "published":
        raise HTTPException(status_code=409, detail="This event is not currently on sale")

    start = _parse_event_start(event)
    if start is not None and start < datetime.now(timezone.utc):
        raise HTTPException(status_code=409, detail="This event has already started")

    stock_left = event.get("stock_left")
    if stock_left is not None and int(stock_left) < quantity:
        raise HTTPException(
            status_code=409,
            detail=f"Only {stock_left} ticket(s) remain for this event",
        )

    created = create_order_service(
        sb=sb,
        external_auth_id=external_auth_id,
        event_id=event_id,
        quantity=quantity,
    )

    risk = created.get("risk") or {}
    if risk.get("review_required"):
        answer = (
            "订单已创建，但风险检查要求进一步验证，因此没有自动执行模拟支付。"
            if lang == "zh"
            else "The order was created, but the risk check requires additional verification, so mock payment was not completed automatically."
        )
        return {
            "answer": answer,
            "answer_mode": "purchase_review",
            "intent": "purchase",
            "lang": lang,
            "citations": [f"event://{event_id}", f"order://{created.get('order_id')}"],
            "scores": [1.0],
            "risk_level": risk.get("risk_level"),
            "risk_score": risk.get("risk_score"),
            "event": event_to_assistant_card(event),
            "order": created,
            "payment": None,
            "next_actions": ["查看订单", "联系人工客服"] if lang == "zh" else ["View order", "Contact support"],
        }

    order_id = created.get("order_id") or created.get("id")
    if not order_id:
        raise HTTPException(status_code=502, detail="Order was created without an order id")

    payment = pay_order_service(sb, external_auth_id, str(order_id))
    answer = (
        f"模拟购票已完成。订单 {order_id} 已支付，{quantity} 张票应已签发到你的票夹中。"
        if lang == "zh"
        else f"Mock purchase completed. Order {order_id} was paid and {quantity} ticket(s) should now be available in your wallet."
    )
    return {
        "answer": answer,
        "answer_mode": "purchase_completed",
        "intent": "purchase",
        "lang": lang,
        "citations": [f"event://{event_id}", f"order://{order_id}"],
        "scores": [1.0],
        "risk_level": risk.get("risk_level"),
        "risk_score": risk.get("risk_score"),
        "event": event_to_assistant_card(event),
        "order": created,
        "payment": payment,
        "next_actions": ["打开票夹", "查看活动聊天室"] if lang == "zh" else ["Open wallet", "Open event chat"],
    }
