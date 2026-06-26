import re
from typing import Dict, List


def detect_language(text: str) -> str:
    if re.search(r"[\u4e00-\u9fff]", text):
        return "zh"
    return "en"


def normalize_question(text: str) -> str:
    return text.strip()


def correct_spelling_en(text: str) -> str:
    try:
        from textblob import TextBlob  # type: ignore
    except Exception:
        return text
    try:
        return str(TextBlob(text).correct())
    except Exception:
        return text


def classify_intent(q: str) -> str:
    q_low = q.lower()
    if any(k in q for k in ["退票", "退款", "退钱", "退费", "退回", "能不能退", "可以退吗", "可以退票吗", "怎么退票", "如何退票", "票能退吗"]) or any(k in q_low for k in ["refund", "money back", "cancel order", "cancel my ticket", "refundable"]):
        return "refund"
    if any(k in q for k in ["转票", "转让", "给朋友", "送给朋友", "改名", "改成别人的名字", "换名字", "换人", "换购票人"]) or any(k in q_low for k in ["transfer", "resell", "give my ticket", "change ticket holder", "change name on ticket"]):
        return "transfer"
    if any(k in q for k in ["入场", "进场", "进门", "检票", "安检", "能带", "可不可以带", "能不能带", "带饮料", "带水", "带酒", "带食物", "吃的", "行李", "背包", "包", "相机", "自拍杆", "禁止携带", "带进去", "电子票", "二维码"]) or any(k in q_low for k in ["entry", "entrance", "door open", "security", "what can i bring", "can i bring", "allowed", "forbidden", "bag", "backpack", "food", "drinks", "bottle", "electronic ticket", "qr code"]):
        return "entry"
    if any(k in q for k in ["票价", "多少钱", "价格", "贵不贵", "服务费", "手续费", "加价", "差价", "优惠", "折扣", "学生票", "vip票", "早鸟", "预售"]) or any(k in q_low for k in ["price", "how much", "ticket cost", "service fee", "extra fee", "discount", "student", "vip", "early bird", "presale"]):
        return "price"
    if any(k in q for k in ["在哪里", "在哪儿", "位置", "地点", "地址", "场馆", "怎么去", "怎么到", "怎么到达", "路线", "地铁", "地铁站", "出口", "几点开始", "什么时候开始", "几点入场", "几点开演", "演出时间"]) or any(k in q_low for k in ["where is the venue", "location", "address", "how to get there", "how do i get there", "when does it start", "what time", "start time", "show time"]):
        return "venue_info"
    if any(k in q for k in ["演出", "音乐会", "演唱会", "live", "活动", "音乐节", "推荐", "有什么好看的", "有什么演出", "看什么", "附近有什么", "附近的演出", "最近有什么演出"]) or any(k in q_low for k in ["show", "concert", "event", "festival", "live", "any events", "what to watch", "recommend", "near me", "gigs", "shows near"]):
        return "event_search"
    return "other"


INTENT_SYNONYMS: Dict[str, List[str]] = {
    "refund": ["refund policy", "ticket refund", "cancel order", "cancel my ticket", "money back"],
    "transfer": ["transfer ticket", "resell ticket", "give my ticket to friend", "change ticket holder"],
    "entry": ["entry rules", "what can I bring", "security check", "bag policy", "food and drinks allowed", "qr code ticket", "electronic ticket"],
    "price": ["ticket price", "service fee", "extra fee", "discount", "student price", "vip price", "early bird ticket"],
    "venue_info": ["where is the venue", "venue location", "address", "how to get there", "start time", "show time"],
}


def expand_query_by_intent(intent: str, q_norm: str, lang: str = "en") -> str:
    if lang == "zh":
        return q_norm
    synonyms = INTENT_SYNONYMS.get(intent)
    return f"{q_norm} {' '.join(synonyms)}" if synonyms else q_norm
