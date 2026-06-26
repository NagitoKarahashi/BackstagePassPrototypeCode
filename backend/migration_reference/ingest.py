import os
import re
import json
from pathlib import Path

import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
import joblib

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
VDB_DIR = BASE_DIR / "vectordb"

CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "500"))   # 按字符长度切块即可
OVERLAP = int(os.getenv("OVERLAP", "50"))


def clean_text(text: str) -> str:
    text = text.replace("\r", " ")
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def split_text(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = OVERLAP):
    """简单按字符切块，避免单块太长。"""
    text = clean_text(text)
    chunks = []
    n = len(text)
    if n == 0:
        return []
    start = 0
    while start < n:
        end = min(n, start + chunk_size)
        chunk = text[start:end]
        chunks.append(chunk)
        if end == n:
            break
        start = max(0, end - overlap)
    return chunks


def load_docs():
    """从 faq/policy/events 读取文本，切成 chunk 列表。"""
    items: list[tuple[str, str]] = []

    # FAQ：按 Q: 开头拆成一组一组的问答
    faq_path = DATA_DIR / "faq.md"
    if faq_path.exists():
        faq_raw = faq_path.read_text(encoding="utf-8")

    # 去掉开头的标题行（如 "# FAQ..."）
        faq_body = re.sub(r"^#.*\n?", "", faq_raw).strip()

    # 按 Q: 分块：每块形如 "Q: ... A: ..."
    # 使用前瞻，保留 "Q:" 本身
        blocks = re.split(r"\n(?=Q\s*:)", faq_body)

        for i, block in enumerate(blocks):
            block = block.strip()
            if not block:
                continue
            items.append((block, f"doc://faq#{i+1}"))


    # Policy
    policy_path = DATA_DIR / "policy.md"
    if policy_path.exists():
        pol = policy_path.read_text(encoding="utf-8")
        for i, c in enumerate(split_text(pol)):
            items.append((c, f"doc://policy#{i+1}"))

    # Events
    events_path = DATA_DIR / "events.csv"
    if events_path.exists():
        ev = pd.read_csv(events_path)
        for _, r in ev.iterrows():
            txt = (
                f"标题:{r['title']} 艺人:{r['artist']} 类型:{r['genre']} "
                f"城市:{r['city']} 时间:{r['start_time']} 描述:{r['desc']}"
            )
            for i, c in enumerate(split_text(txt, chunk_size=300, overlap=30)):
                items.append((c, f"doc://event#{r['event_id']}#{i+1}"))

    return items


def main():
    os.makedirs(VDB_DIR, exist_ok=True)

    items = load_docs()
    if not items:
        print("No data loaded from data/ directory.")
        return

    texts = [t for t, _ in items]
    metas = [m for _, m in items]

    print(f"Loaded {len(texts)} text chunks. Building TF-IDF matrix...")

    # 构建 TF-IDF 向量矩阵
    vectorizer = TfidfVectorizer(
        analyzer="char",         # 按字符切
        ngram_range=(2, 4),      # 2~4 字符的片段，比如 "退票", "怎么退", "能否退票"
        min_df=1,
        max_features=30000,
    )
    X = vectorizer.fit_transform(texts)


    print(f"TF-IDF matrix shape: {X.shape}")

    # 保存 vectorizer 与矩阵及元数据
    joblib.dump(
        {
            "vectorizer": vectorizer,
            "matrix": X,
            "meta": [{"text": t, "source": m} for t, m in items],
        },
        VDB_DIR / "tfidf_store.pkl",
    )

    print(f"Saved TF-IDF store → {VDB_DIR / 'tfidf_store.pkl'}")


if __name__ == "__main__":
    main()
