from typing import Any, Dict, List, Optional
from app.services.events_service import get_events_df

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
    lines.append("根据你的城市和兴趣，我们为你推荐以下演出：\n" if lang == "zh" else "Here are some events we recommend based on your city and interests:\n")
    for r in recs:
        if lang == "zh":
            block = (f"🎵 {r['title']}\n• 艺人: {r['artist']}\n• 类型: {r['genre']}\n• 城市: {r['city']}\n• 时间: {r['start_time']}\n• 描述: {r['desc']}\n")
        else:
            block = (f"🎵 {r['title']}\n• Artist: {r['artist']}\n• Genre: {r['genre']}\n• City: {r['city']}\n• Date: {r['start_time']}\n• Description: {r['desc']}\n")
        lines.append(block)
    return "\n".join(lines)


def recommend_events(question: str, context: Dict[str, Any]) -> List[Dict[str, Any]]:
    events_df = get_events_df()
    if events_df.empty:
        return []
    q_city = infer_city_from_text(question)
    ctx_city = context.get("city")
    liked_tags_low = [t.lower() for t in (context.get("liked_tags") or [])]
    genre = infer_genre_from_text(question)
    rows: List[Dict[str, Any]] = []
    for _, r in events_df.iterrows():
        score = 0.01
        if ctx_city and str(r["city"]).lower() == str(ctx_city).lower():
            score += 1.5
        elif q_city and r["city"] == q_city:
            score += 1.2
        elif q_city and str(r["city"]).lower() in q_city.lower():
            score += 0.8
        r_genre = str(r.get("genre", "")).lower()
        if genre and r_genre == genre:
            score += 1.0
        if any(tag in r_genre for tag in liked_tags_low):
            score += 0.8
        row = r.to_dict()
        row["score"] = score
        rows.append(row)
    rows = [r for r in rows if r["score"] > 0.0]
    rows.sort(key=lambda x: x["score"], reverse=True)
    return rows[:5]
