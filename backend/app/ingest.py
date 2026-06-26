import os
import re
from pathlib import Path

import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
import joblib

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
VDB_DIR = BASE_DIR / "vectordb"

CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "500"))
OVERLAP = int(os.getenv("OVERLAP", "50"))


def clean_text(text: str) -> str:
    text = text.replace("\r", " ")
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def split_text(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = OVERLAP):
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


def parse_faq_blocks(faq_raw: str):
    """
    将 FAQ 文本解析为 block：
    支持这种结构：
        Q: ...
        Q: ...
        Q: ...
        A: ...
    每组连续 Q + 一个 A 作为一个 block。
    """
    faq_body = re.sub(r"^#.*\n?", "", faq_raw).strip()
    lines = [line.rstrip() for line in faq_body.splitlines()]

    blocks = []
    current_questions = []
    current_answer = []

    def flush_block():
        nonlocal current_questions, current_answer
        if current_questions:
            block_lines = []
            block_lines.extend(current_questions)
            if current_answer:
                block_lines.extend(current_answer)
            blocks.append("\n".join(block_lines).strip())
        current_questions = []
        current_answer = []

    in_answer = False

    for raw_line in lines:
        line = raw_line.strip()
        if not line:
            if in_answer and current_answer:
                current_answer.append("")
            continue

        if re.match(r"^Q\s*:", line, flags=re.IGNORECASE):
            # 如果已经有 Q 和 A，说明进入下一组 FAQ
            if current_questions and current_answer:
                flush_block()
            current_questions.append(line)
            in_answer = False
            continue

        if re.match(r"^(A|A_ZH|A_EN)\s*:", line, flags=re.IGNORECASE):
            current_answer.append(line)
            in_answer = True
            continue

        # 普通续行
        if in_answer:
            current_answer.append(line)
        elif current_questions:
            # 少数情况下 Q 文本换行，拼到最后一个 Q 上
            current_questions[-1] = current_questions[-1] + " " + line

    flush_block()
    return [b for b in blocks if b.strip()]


def load_docs():
    items: list[tuple[str, str]] = []

    # FAQ
    faq_path = DATA_DIR / "faq.md"
    if faq_path.exists():
        faq_raw = faq_path.read_text(encoding="utf-8")
        faq_blocks = parse_faq_blocks(faq_raw)
        for i, block in enumerate(faq_blocks):
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

    print(f"Loaded {len(texts)} text chunks. Building TF-IDF matrix...")

    vectorizer = TfidfVectorizer(
        analyzer="char",
        ngram_range=(2, 4),
        min_df=1,
        max_features=30000,
    )
    X = vectorizer.fit_transform(texts)

    print(f"TF-IDF matrix shape: {X.shape}")

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