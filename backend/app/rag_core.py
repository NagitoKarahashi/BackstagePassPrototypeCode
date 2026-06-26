import os
import json
from pathlib import Path

import numpy as np
import joblib
from sklearn.metrics.pairwise import cosine_similarity

BASE_DIR = Path(__file__).resolve().parent.parent
VDB_DIR = BASE_DIR / "vectordb"

TOP_K = int(os.getenv("TOP_K", "4"))


class RAGCore:
    def __init__(self, k: int = TOP_K):
        store_path = VDB_DIR / "tfidf_store.pkl"
        if not store_path.exists():
            raise RuntimeError(f"TF-IDF store not found: {store_path}, please run ingest.py first.")
        store = joblib.load(store_path)
        self.vectorizer = store["vectorizer"]
        self.matrix = store["matrix"]   # (num_docs, num_features) sparse
        self.meta = store["meta"]
        self.k = k

    def retrieve(self, query: str):
        # 将查询转换成 TF-IDF 向量
        q_vec = self.vectorizer.transform([query])  # shape: (1, num_features)

        # 计算与所有文档的余弦相似度
        sims = cosine_similarity(q_vec, self.matrix)[0]  # shape: (num_docs,)

        # 取得相似度最高的前 K 个索引
        top_idx = np.argsort(sims)[::-1][: self.k]
        top_scores = sims[top_idx].tolist()
        ctx = [self.meta[i] for i in top_idx]
        return ctx, top_scores

    def build_prompt(self, question: str, contexts, user_ctx: dict | None = None):
        prefix = (
            "你是演出售票助手，只能依据下列资料回答；如果资料不足，"
            "请简洁说明不确定并提示用户查看FAQ或联系人工客服。回答请标注引用编号，如[1][2]。"
        )
        personal = ""
        if user_ctx:
            personal = f"\n[用户上下文] city={user_ctx.get('city')}, likes={user_ctx.get('liked_tags')}"
        kn = "\n\n".join(
            [f"[{i+1}] {c['text']}\n(来源:{c['source']})" for i, c in enumerate(contexts)]
        )
        return (
            f"{prefix}{personal}\n\n[知识库]\n{kn}\n\n"
            f"[问题]\n{question}\n\n请用中文回答，并在句尾列出引用编号。"
        )
