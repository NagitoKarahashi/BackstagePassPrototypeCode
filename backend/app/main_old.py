import os
import re
import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from collections import defaultdict
from datetime import datetime

import numpy as np
import pandas as pd
import joblib
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from sklearn.metrics.pairwise import cosine_similarity
from rank_bm25 import BM25Okapi

# ---------------------------
# Paths
# ---------------------------
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
VDB_DIR = BASE_DIR / "vectordb"
TFIDF_PATH = VDB_DIR / "tfidf_store.pkl"

# ---------------------------
# 载入 TF-IDF 知识库
# ---------------------------
if TFIDF_PATH.exists():
    store = joblib.load(TFIDF_PATH)
    VECTORIZER = store["vectorizer"]
    MATRIX = store["matrix"]
    META = store["meta"]          # 每一项形如 {"text": "...", "source": "doc://xxx"}
    RAG_ENABLED = True
    print(f"[INFO] Loaded TF-IDF store: matrix={MATRIX.shape}, meta={len(META)}")
else:
    print(f"[WARN] TF-IDF store not found at {TFIDF_PATH}, RAG disabled.")
    VECTORIZER = None
    MATRIX = None
    META: List[Dict[str, Any]] = []
    RAG_ENABLED = False

# ---------------------------
# 构建 BM25 语料（只在 RAG 可用时）
# ---------------------------
def tokenize_for_bm25(text: str) -> List[str]:
    """
    简单分词：
    - 英文：按单词
    - 中文：按单字
    """
    text = text.lower()
    # 匹配：单个中文字符 或 一段连续的字母数字
    tokens = re.findall(r"[\u4e00-\u9fff]|[a-z0-9]+", text)
    return tokens

if RAG_ENABLED and META:
    CORPUS_TEXTS: List[str] = [m["text"] for m in META]
    CORPUS_TOKENS: List[List[str]] = [tokenize_for_bm25(t) for t in CORPUS_TEXTS]
    BM25 = BM25Okapi(CORPUS_TOKENS)
    print(f"[INFO] BM25 corpus built: {len(CORPUS_TOKENS)} docs")
else:
    CORPUS_TEXTS = []
    BM25 = None
    print("[WARN] BM25 disabled because TF-IDF store is not loaded.")

# ---------------------------
# Utils: language detection
# ---------------------------
def detect_language(text: str) -> str:
    """
    非常简单的语言检测：
    - 包含中文字符 → 'zh'
    - 否则 → 'en'
    """
    if re.search(r"[\u4e00-\u9fff]", text):
        return "zh"
    return "en"


def normalize_question(text: str) -> str:
    text = text.strip()
    # 不强制小写，中文没必要
    return text


# ---------------------------
# Spell correction (English only, safe fallback)
# ---------------------------
def correct_spelling_en(text: str) -> str:
    """
    只对英文做简单拼写纠错。
    如果 textblob 不存在，直接原样返回，避免报错。
    """
    try:
        from textblob import TextBlob  # type: ignore
    except Exception:
        return text

    try:
        blob = TextBlob(text)
        return str(blob.correct())
    except Exception:
        return text

# ---------------------------
# Event loading & reload
# ---------------------------
def load_events_df() -> pd.DataFrame:
    events_path = DATA_DIR / "events.csv"
    if not events_path.exists():
        print(f"[WARN] events.csv not found at {events_path}, using empty DataFrame.")
        return pd.DataFrame(
            columns=["event_id", "title", "artist", "genre", "city", "start_time", "desc"]
        )
    df = pd.read_csv(events_path)
    expected_cols = ["event_id", "title", "artist", "genre", "city", "start_time", "desc"]
    missing = [c for c in expected_cols if c not in df.columns]
    if missing:
        print(f"[WARN] events.csv missing columns: {missing}")
    return df


EVENTS_DF = load_events_df()


# ---------------------------
# Intent classification (EN + ZH 强化版)
# ---------------------------
def classify_intent(q: str) -> str:
    """
    简单规则意图分类：
    - refund / transfer / entry / price / venue_info / event_search / other
    """
    q_low = q.lower()

    # Refund / 退票相关
    if any(k in q for k in [
        "退票", "退款", "退钱", "退费", "退回",
        "能不能退", "可以退吗", "可以退票吗", "怎么退票", "如何退票", "票能退吗",
    ]) or any(k in q_low for k in [
        "refund", "money back", "cancel order", "cancel my ticket", "refundable",
    ]):
        return "refund"

    # Transfer / 转票相关
    if any(k in q for k in [
        "转票", "转让", "给朋友", "送给朋友",
        "改名", "改成别人的名字", "换名字", "换人", "换购票人",
    ]) or any(k in q_low for k in [
        "transfer", "resell", "give my ticket", "change ticket holder",
        "change name on ticket",
    ]):
        return "transfer"

    # Entry / 入场与安检
    if any(k in q for k in [
        "入场", "进场", "进门", "检票", "安检",
        "能带", "可不可以带", "能不能带",
        "带饮料", "带水", "带酒", "带食物", "吃的",
        "行李", "背包", "包", "相机", "自拍杆",
        "禁止携带", "带进去", "电子票", "二维码",
    ]) or any(k in q_low for k in [
        "entry", "entrance", "door open", "security",
        "what can i bring", "can i bring", "allowed", "forbidden",
        "bag", "backpack", "food", "drinks", "bottle",
        "electronic ticket", "qr code",
    ]):
        return "entry"

    # Price / 票价与费用
    if any(k in q for k in [
        "票价", "多少钱", "价格", "贵不贵",
        "服务费", "手续费", "加价", "差价",
        "优惠", "折扣", "学生票", "vip票", "早鸟", "预售",
    ]) or any(k in q_low for k in [
        "price", "how much", "ticket cost", "service fee", "extra fee",
        "discount", "student", "vip", "early bird", "presale",
    ]):
        return "price"

    # Venue info / 场馆位置与时间
    if any(k in q for k in [
        "在哪里", "在哪儿", "位置", "地点", "地址", "场馆",
        "怎么去", "怎么到", "怎么到达", "路线", "地铁", "地铁站", "出口",
        "几点开始", "什么时候开始", "几点入场", "几点开演", "演出时间",
    ]) or any(k in q_low for k in [
        "where is the venue", "location", "address", "how to get there",
        "how do i get there", "when does it start", "what time",
        "start time", "show time",
    ]):
        return "venue_info"

    # Event search / recommendation 演出搜索与推荐
    if any(k in q for k in [
        "演出", "音乐会", "演唱会", "live", "活动", "音乐节",
        "推荐", "有什么好看的", "有什么演出", "看什么", "附近有什么",
        "附近的演出", "最近有什么演出",
    ]) or any(k in q_low for k in [
        "show", "concert", "event", "festival", "live",
        "any events", "what to watch", "recommend", "near me",
        "gigs", "shows near",
    ]):
        return "event_search"

    return "other"


# ---------------------------
# Intent synonyms for EN (RAG expansion)
# ---------------------------
INTENT_SYNONYMS: Dict[str, List[str]] = {
    "refund": [
        "refund policy", "ticket refund", "cancel order", "cancel my ticket",
        "money back",
    ],
    "transfer": [
        "transfer ticket", "resell ticket", "give my ticket to friend",
        "change ticket holder",
    ],
    "entry": [
        "entry rules", "what can I bring", "security check", "bag policy",
        "food and drinks allowed", "qr code ticket", "electronic ticket",
    ],
    "price": [
        "ticket price", "service fee", "extra fee", "discount", "student price",
        "vip price", "early bird ticket",
    ],
    "venue_info": [
        "where is the venue", "venue location", "address", "how to get there",
        "start time", "show time",
    ],
}


def expand_query_by_intent(intent: str, q_norm: str, lang: str = "en") -> str:
    """
    根据 intent 扩展检索 query：
    - 英文：附加同义短语，提升“同义问法”命中率
    - 中文：通常不扩展，直接用原问题，以免引入太多英文噪声
    """
    if lang == "zh":
        return q_norm

    if intent in INTENT_SYNONYMS:
        synonyms = " ".join(INTENT_SYNONYMS[intent])
        return f"{q_norm} {synonyms}"
    return q_norm


# ---------------------------
# Genre & City keywords for推荐
# ---------------------------
GENRE_KEYWORDS: Dict[str, List[str]] = {
    "edm": ["edm", "electronic", "rave", "dj", "techno", "club", "电子"],
    "indie": ["indie", "alternative", "underground", "band", "独立", "独立摇滚"],
    "jazz": ["jazz", "blue note", "fusion", "爵士"],
    "rock": ["rock", "metal", "punk", "摇滚"],
    "pop": ["pop", "k-pop", "top hits", "chart", "流行"],
    "classic": ["classic", "classical", "symphony", "orchestra", "philharmonic", "古典"],
}

CITY_KEYWORDS: Dict[str, List[str]] = {
    "Taipei": ["taipei", "taiwan", "台北"],
    "Kaohsiung": ["kaohsiung", "高雄"],
    "Hong Kong": ["hong kong", "hk", "香港"],
    "Shenzhen": ["shenzhen", "深圳"],
    "Guangzhou": ["guangzhou", "广州"],
    "Tokyo": ["tokyo", "东京"],
    "Seoul": ["seoul", "首尔", "首爾"],
    "Singapore": ["singapore", "新加坡"],
    "Bangkok": ["bangkok", "曼谷"],
}


def infer_genre_from_text(text: str) -> Optional[str]:
    t_low = text.lower()
    for g, kws in GENRE_KEYWORDS.items():
        if any(k in t_low for k in kws):
            return g
    return None


def infer_city_from_text(text: str) -> Optional[str]:
    t_low = text.lower()
    for city, kws in CITY_KEYWORDS.items():
        if any(k in t_low for k in kws):
            return city
    return None


def format_recommendations(recs: List[Dict[str, Any]], lang: str = "en") -> str:
    if not recs:
        return ""

    lines: List[str] = []
    if lang == "zh":
        lines.append("根据你的城市和兴趣，我们为你推荐以下演出：\n")
    else:
        lines.append("Here are some events we recommend based on your city and interests:\n")

    for r in recs:
        if lang == "zh":
            block = (
                f"🎵 {r['title']}\n"
                f"• 艺人: {r['artist']}\n"
                f"• 类型: {r['genre']}\n"
                f"• 城市: {r['city']}\n"
                f"• 时间: {r['start_time']}\n"
                f"• 描述: {r['desc']}\n"
            )
        else:
            block = (
                f"🎵 {r['title']}\n"
                f"• Artist: {r['artist']}\n"
                f"• Genre: {r['genre']}\n"
                f"• City: {r['city']}\n"
                f"• Date: {r['start_time']}\n"
                f"• Description: {r['desc']}\n"
            )
        lines.append(block)

    return "\n".join(lines)


def recommend_events(question: str, context: Dict[str, Any]) -> List[Dict[str, Any]]:
    if EVENTS_DF.empty:
        return []

    q_city = infer_city_from_text(question)
    ctx_city = context.get("city")
    liked_tags: List[str] = context.get("liked_tags") or []

    genre = infer_genre_from_text(question)
    liked_tags_low = [t.lower() for t in liked_tags]

    rows: List[Dict[str, Any]] = []
    for _, r in EVENTS_DF.iterrows():
        score = 0.0

        # City score
        if ctx_city and str(r["city"]).lower() == str(ctx_city).lower():
            score += 1.5
        elif q_city and r["city"] == q_city:
            score += 1.2
        elif q_city and str(r["city"]).lower() in q_city.lower():
            score += 0.8

        # Genre score
        r_genre = str(r.get("genre", "")).lower()
        if genre and r_genre == genre:
            score += 1.0
        if any(tag in r_genre for tag in liked_tags_low):
            score += 0.8

        # 时间：越近越好（简单处理：靠 start_time 排）
        score += 0.01  # baseline

        row = r.to_dict()
        row["score"] = score
        rows.append(row)

    rows = [r for r in rows if r["score"] > 0.0]
    rows.sort(key=lambda x: x["score"], reverse=True)
    return rows[:5]

# ---------------------------
# Pydantic models
# ---------------------------


class AskRequest(BaseModel):
    question: str
    context: Optional[Dict[str, Any]] = None


class OrderInfo(BaseModel):
    """
    一次购票请求的基本信息（原型版）
    未来可接入真实后端 / 区块链订单。
    """
    user_id: str
    event_id: str
    quantity: int
    price_per_ticket: float
    currency: str = "USD"

    wallet_address: Optional[str] = None
    device_id: Optional[str] = None
    ip: Optional[str] = None

    # 允许客户端传时间（ISO8601），没有就用服务器当前时间
    timestamp: Optional[str] = None


# 简单的内存内统计，用于规则判断（真实系统应放到数据库里）
WALLET_EVENT_COUNTS = defaultdict(int)   # (wallet, event_id) -> count
IP_EVENT_COUNTS = defaultdict(int)       # (ip, event_id) -> count
USER_DAILY_COUNTS = defaultdict(int)     # (user_id, YYYY-MM-DD) -> total_qty

def evaluate_fraud(order: OrderInfo) -> Dict[str, Any]:
    """
    简单规则版风控评分：
    返回 risk_score [0,1]、risk_level、reason 列表、特征和建议动作/提示信息。
    """
    score = 0.0
    reasons: List[str] = []

    # 1. 时间处理
    if order.timestamp:
        try:
            ts = datetime.fromisoformat(order.timestamp)
        except Exception:
            ts = datetime.utcnow()
            reasons.append("Invalid timestamp format, fallback to server time.")
    else:
        ts = datetime.utcnow()

    day_key = ts.strftime("%Y-%m-%d")

    # 2. 更新统计计数（原型：内存计数）
    if order.wallet_address:
        key_w = (order.wallet_address.lower(), order.event_id)
        WALLET_EVENT_COUNTS[key_w] += order.quantity

    if order.ip:
        key_ip = (order.ip, order.event_id)
        IP_EVENT_COUNTS[key_ip] += order.quantity

    key_user_day = (order.user_id, day_key)
    USER_DAILY_COUNTS[key_user_day] += order.quantity

    total_amount = order.price_per_ticket * order.quantity

    # 3. 规则 1：单次购票数量过大
    if order.quantity >= 6:
        score += 0.3
        reasons.append(f"High quantity in a single order: {order.quantity} tickets.")

    # 4. 规则 2：单笔金额较大
    if total_amount >= 500:
        score += 0.2
        reasons.append(f"High total amount: {total_amount:.2f} {order.currency}.")

    # 5. 规则 3：同一钱包对同一活动的总购票量过高
    wallet_event_count = None
    if order.wallet_address:
        key_w = (order.wallet_address.lower(), order.event_id)
        wallet_event_count = WALLET_EVENT_COUNTS[key_w]
        if wallet_event_count >= 10:
            score += 0.3
            reasons.append(
                f"Wallet {order.wallet_address} purchased {wallet_event_count} tickets "
                f"for event {order.event_id} in total."
            )

    # 6. 规则 4：同一 IP 对同一活动的购票量过高
    ip_event_count = None
    if order.ip:
        key_ip = (order.ip, order.event_id)
        ip_event_count = IP_EVENT_COUNTS[key_ip]
        if ip_event_count >= 8:
            score += 0.3
            reasons.append(
                f"IP {order.ip} purchased {ip_event_count} tickets for event {order.event_id}."
            )

    # 7. 规则 5：同一用户当天购票量过多
    daily_count = USER_DAILY_COUNTS[key_user_day]
    if daily_count >= 15:
        score += 0.2
        reasons.append(
            f"User {order.user_id} purchased {daily_count} tickets on {day_key}."
        )

    # 8. 分数裁剪到 [0, 1]
    score = max(0.0, min(1.0, score))

    # 9. 风险等级
    if score >= 0.7:
        level = "high"
    elif score >= 0.4:
        level = "medium"
    else:
        level = "low"

    # 10. 给用户 / 系统的提示与建议动作
    if level == "high":
        recommended_action = "block_or_manual_review"
        user_message = (
            "We detected unusual activity related to your account or device for this event. "
            "For your security, some actions may be temporarily limited. "
            "If this was not you, please review your account activity and contact support."
        )
    elif level == "medium":
        recommended_action = "show_warning"
        user_message = (
            "We noticed some unusual ticket purchase patterns. "
            "Please make sure you are following our ticketing policy and avoid bulk reselling."
        )
    else:
        recommended_action = "allow"
        user_message = ""

    # 11. flags：标记可疑的 user / wallet / ip（原型，只做简单标记）
    flags: Dict[str, Any] = {
        "flag_user": level in ("medium", "high"),
        "flag_wallet": wallet_event_count is not None and wallet_event_count >= 10,
        "flag_ip": ip_event_count is not None and ip_event_count >= 20,
    }

    features = {
        "total_amount": total_amount,
        "user_daily_count": daily_count,
        "wallet_event_count": wallet_event_count,
        "ip_event_count": ip_event_count,
    }

    return {
        "risk_score": score,
        "risk_level": level,
        "reasons": reasons,
        "features": features,
        "flags": flags,
        "recommended_action": recommended_action,
        "user_message": user_message,
        "timestamp_used": ts.isoformat(),
    }

# ---------------------------
# Answer formatting for RAG
# ---------------------------
def clean_answer_text(text: str) -> str:
    """
    对 FAQ 块稍微清洗一下：
    - 去掉多余空白
    """
    text = text.replace("\r", " ")
    text = re.sub(r"\s+", " ", text)
    return text.strip()


# ---------------------------
# FastAPI app
# ---------------------------
app = FastAPI(title="Event Engagement Assistant")


@app.post("/fraud/check_order")
def fraud_check(order: OrderInfo) -> Dict[str, Any]:
    """
    原型风控接口：
    - 输入一笔订单信息
    - 输出 risk_score / risk_level / reasons / features

    后续可以在此处接入真实数据库、区块链数据、ML 模型等。
    """
    result = evaluate_fraud(order)
    return {
        "order": order.dict(),
        "evaluation": result,
    }


@app.get("/health")
def health():
    return {
        "status": "ok",
        "events_rows": int(len(EVENTS_DF)),
        "rag_enabled": bool(RAG_ENABLED),
    }

@app.post("/admin/reload_events")
def reload_events():
    """
    Reload events.csv into memory without restarting the server.
    (仅刷新推荐系统使用的 EVENTS_DF，不重新构建 RAG 向量库)
    """
    global EVENTS_DF
    try:
        EVENTS_DF = load_events_df()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to reload events: {e}")

    return {
        "status": "ok",
        "rows": int(len(EVENTS_DF)),
    }


# ---------------------------
# Web3 wallet mock endpoint
# ---------------------------
@app.get("/wallet/{address}/tickets")
def get_wallet_tickets(address: str) -> Dict[str, Any]:
    """
    Mock Web3 endpoint:
    - 根据钱包地址返回一些「NFT 票」示例
    - 这里只是 demo，不连真实链
    """
    if EVENTS_DF.empty:
        return {"address": address, "tickets": []}

    sample_events = EVENTS_DF.sample(n=min(3, len(EVENTS_DF)), random_state=42)

    tickets = []
    for _, row in sample_events.iterrows():
        tickets.append({
            "nft_id": f"nft_{row['event_id']}",
            "event_id": row["event_id"],
            "title": row["title"],
            "artist": row["artist"],
            "genre": row["genre"],
            "city": row["city"],
            "start_time": row["start_time"],
            "desc": row["desc"],
            "chain": "Polygon (testnet)",
            "contract_address": "0xDEADBEEFDEADBEEFDEADBEEFDEADBEEFDEAD0001",
            "token_standard": "ERC-721",
            "status": "valid",
        })

    return {
        "address": address,
        "tickets": tickets,
    }

def normalize_scores(arr: np.ndarray) -> np.ndarray:
    """简单做一下 max 归一化，避免分数尺度差太多。"""
    if arr.size == 0:
        return arr
    maxv = float(arr.max())
    if maxv <= 0:
        return np.zeros_like(arr)
    return arr / maxv


def hybrid_search(query: str, top_k: int = 5, alpha: float = 0.6) -> List[Dict[str, Any]]:
    """
    使用 TF-IDF + BM25 的混合检索：
        final_score = alpha * tfidf_norm + (1 - alpha) * bm25_norm

    返回按 final_score 排序后的前 top_k 条结果：
        [{"text": ..., "source": ..., "tfidf_score": ..., "bm25_score": ..., "score": ...}, ...]
    """
    if not RAG_ENABLED or VECTORIZER is None or MATRIX is None or BM25 is None:
        return []

    # 1) TF-IDF raw scores
    q_vec = VECTORIZER.transform([query])          # shape: (1, n_features)
    tfidf_raw = (MATRIX @ q_vec.T).toarray().ravel()  # shape: (n_docs,)

    # 2) BM25 raw scores
    q_tokens = tokenize_for_bm25(query)
    bm25_raw = np.array(BM25.get_scores(q_tokens))     # shape: (n_docs,)

    # 3) 归一化
    tfidf_norm = normalize_scores(tfidf_raw)
    bm25_norm = normalize_scores(bm25_raw)

    # 4) 混合
    final_scores = alpha * tfidf_norm + (1.0 - alpha) * bm25_norm

    # 5) 取前 top_k
    idx_sorted = np.argsort(-final_scores)[:top_k]

    results: List[Dict[str, Any]] = []
    for i in idx_sorted:
        results.append({
            "text": CORPUS_TEXTS[i],
            "source": META[i]["source"],
            "tfidf_score": float(tfidf_norm[i]),
            "bm25_score": float(bm25_norm[i]),
            "score": float(final_scores[i]),
        })
    return results

# ---------------------------
# Main /ask endpoint
# ---------------------------

@app.post("/ask")
def ask(req: AskRequest) -> Dict[str, Any]:
    # 1) 语言检测
    lang = detect_language(req.question)

    # 2) 拼写纠错（仅英文）
    if lang == "en":
        corrected = correct_spelling_en(req.question)
    else:
        corrected = req.question

    q_norm = normalize_question(corrected)
    user_ctx = req.context or {}

    # 2.5) 读取风控上下文（如果有）
    risk_info = user_ctx.get("risk") or {}
    risk_level = risk_info.get("risk_level")          # "low" / "medium" / "high" / None
    risk_score = risk_info.get("risk_score")
    risk_user_message = risk_info.get("user_message")

    # 3) 意图分类
    intent = classify_intent(q_norm)

    # 4) Event search / recommendation（带风控行为）
    if intent == "event_search":
        recs = recommend_events(q_norm, user_ctx)
        if not recs:
            if lang == "zh":
                answer = (
                    "在当前数据集中，没有找到与你条件匹配的近期演出。"
                    "你可以尝试更换城市、时间范围或音乐类型再试一次。"
                )
            else:
                answer = (
                    "I couldn't find any upcoming events that match your query in the current dataset. "
                    "Please try another city, date range, or genre."
                )
            return {
                "answer": answer,
                "citations": [],
                "scores": [],
                "intent": intent,
                "lang": lang,
                "risk_level": risk_level,
                "risk_score": risk_score,
            }

        # 根据风险等级调整行为 & 提示
        warning_lines: list[str] = []

        if risk_level == "high":
            # 高风险：减少推荐数量 + 强提示
            recs = recs[:3]
            if lang == "zh":
                warning_lines.append(
                    "⚠️ 系统检测到你的账号或设备存在异常购票行为，部分操作可能被限制。"
                    "如非本人操作，请尽快检查账号安全并联系人工客服。"
                )
            else:
                warning_lines.append(
                    "⚠️ Our system detected unusual purchase patterns on your account or device. "
                    "Some actions may be limited. If this was not you, please review your account "
                    "activity and contact support."
                )
        elif risk_level == "medium":
            # 中风险：仅提示，不减推荐
            if lang == "zh":
                warning_lines.append(
                    "⚠️ 我们注意到你的购票行为略有异常，请避免批量转售或代购，以免触发风控限制。"
                )
            else:
                warning_lines.append(
                    "⚠️ We noticed some slightly unusual ticket purchase patterns. "
                    "Please avoid bulk reselling or brokering to prevent further restrictions."
                )

        # 如果风控模块返回了更具体的 user_message，一并展示
        if risk_user_message:
            warning_lines.append(risk_user_message)

        rec_text = format_recommendations(recs, lang=lang)

        if warning_lines:
            answer = "\n".join(warning_lines) + "\n\n" + rec_text
        else:
            answer = rec_text

        citations = [f"event://{r['event_id']}" for r in recs]
        scores = [r["score"] for r in recs]

        return {
            "answer": answer,
            "citations": citations,
            "scores": scores,
            "intent": intent,
            "lang": lang,
            "risk_level": risk_level,
            "risk_score": risk_score,
        }

    # 5) RAG FAQ / policy 问答
    search_query = expand_query_by_intent(intent, q_norm, lang=lang)
    ctx, scores = RAG.retrieve(search_query)

    if not ctx:
        if lang == "zh":
            core_answer = (
                "抱歉，在当前知识库中没有找到与你的问题足够相关的信息。"
                "请查看 FAQ 页面或联系人工客服。"
            )
        else:
            core_answer = (
                "Sorry, I couldn't find information closely related to your question "
                "in the current knowledge base. Please check the FAQ or contact support."
            )
        return {
            "answer": core_answer,
            "citations": [],
            "scores": [],
            "intent": intent,
            "lang": lang,
            "risk_level": risk_level,
            "risk_score": risk_score,
        }

    best_score = scores[0] if scores else 0.0

    if best_score < 0.05:
        if lang == "zh":
            core_answer = (
                "抱歉，根据当前 FAQ/政策内容，我没有找到足够匹配的问题。"
                "请查看 FAQ 页面或联系人工客服获取更详细的说明。"
            )
        else:
            core_answer = (
                "Sorry, I couldn't find a confident match for your question in the current FAQ/policy data. "
                "Please check the FAQ page or contact support for more details."
            )
        return {
            "answer": core_answer,
            "citations": [c["source"] for c in ctx],
            "scores": scores,
            "intent": intent,
            "lang": lang,
            "risk_level": risk_level,
            "risk_score": risk_score,
        }

    primary = clean_answer_text(ctx[0]["text"])
    core_answer = primary

    # 如果风险不低，在回答前加统一风险提示 Banner
    if risk_level in ("medium", "high"):
        if lang == "zh":
            risk_banner = (
                "⚠️ 提示：系统检测到你的账号或设备存在一定风险，"
                "为保证账号和票务安全，部分操作可能需要额外验证或被限制。\n"
            )
        else:
            risk_banner = (
                "⚠️ Note: Our system detected some risk signals related to your account or device. "
                "For your security, some actions may require additional verification or limitations.\n"
            )
        core_answer = risk_banner + "\n" + core_answer

    return {
        "answer": core_answer,
        "citations": [c["source"] for c in ctx],
        "scores": scores,
        "intent": intent,
        "lang": lang,
        "risk_level": risk_level,
        "risk_score": risk_score,
    }
