import re
from typing import Any, Dict, List, Optional

import joblib
import numpy as np
from rank_bm25 import BM25Okapi

from app.core.config import TFIDF_PATH


def tokenize_for_bm25(text: str) -> List[str]:
    return re.findall(r"[\u4e00-\u9fff]|[a-z0-9]+", text.lower())


def normalize_scores(arr: np.ndarray) -> np.ndarray:
    if arr.size == 0:
        return arr
    maxv = float(arr.max())
    return np.zeros_like(arr) if maxv <= 0 else arr / maxv


class HybridRetriever:
    def __init__(self) -> None:
        self.enabled = False
        self.vectorizer = None
        self.matrix = None
        self.meta: List[Dict[str, Any]] = []
        self.corpus_texts: List[str] = []
        self.bm25: Optional[BM25Okapi] = None
        self.reload()

    def reload(self) -> None:
        if not TFIDF_PATH.exists():
            self.enabled = False
            self.vectorizer = None
            self.matrix = None
            self.meta = []
            self.corpus_texts = []
            self.bm25 = None
            return

        store = joblib.load(TFIDF_PATH)
        self.vectorizer = store["vectorizer"]
        self.matrix = store["matrix"]
        self.meta = store["meta"]
        self.corpus_texts = [m["text"] for m in self.meta]

        corpus_tokens = [tokenize_for_bm25(t) for t in self.corpus_texts]
        self.bm25 = BM25Okapi(corpus_tokens) if corpus_tokens else None
        self.enabled = True

    def search(
        self,
        query: str,
        top_k: int = 5,
        alpha: float = 0.6,
        source_prefixes: Optional[List[str]] = None,
        min_score: float = 0.0,
    ) -> List[Dict[str, Any]]:
        if (
            not self.enabled
            or self.vectorizer is None
            or self.matrix is None
            or self.bm25 is None
        ):
            return []

        q_vec = self.vectorizer.transform([query])
        tfidf_raw = (self.matrix @ q_vec.T).toarray().ravel()
        bm25_raw = np.array(self.bm25.get_scores(tokenize_for_bm25(query)))

        tfidf_norm = normalize_scores(tfidf_raw)
        bm25_norm = normalize_scores(bm25_raw)
        final_scores = alpha * tfidf_norm + (1.0 - alpha) * bm25_norm

        idx_sorted = np.argsort(-final_scores)

        results: List[Dict[str, Any]] = []
        for i in idx_sorted:
            score = float(final_scores[i])
            source = self.meta[i]["source"]

            if score <= min_score:
                continue

            if source_prefixes and not any(str(source).startswith(p) for p in source_prefixes):
                continue

            results.append(
                {
                    "text": self.corpus_texts[i],
                    "source": source,
                    "tfidf_score": float(tfidf_norm[i]),
                    "bm25_score": float(bm25_norm[i]),
                    "score": score,
                }
            )

            if len(results) >= top_k:
                break

        return results


retriever = HybridRetriever()