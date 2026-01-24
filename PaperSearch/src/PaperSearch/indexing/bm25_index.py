# bm25_index.py

import math
import re
from collections import Counter, defaultdict
from typing import Dict, List, Tuple

from .normalizer import normalize_text


def tokenize(text: str) -> List[str]:
    return re.findall(r"[a-z0-9]+", text.lower())


class BM25Index:
    """
    Lightweight BM25 index with synonym expansion and concept metadata.
    """

    def __init__(self, k1: float = 1.5, b: float = 0.75):
        self.k1 = k1
        self.b = b

        self.N = 0
        self.doc_len: Dict[int, int] = {}
        self.avg_len: float = 0.0

        self.df: Counter = Counter()
        self.inverted: Dict[str, List[Tuple[int, int]]] = defaultdict(list)
        self.doc_ids: Dict[int, str] = {}

        self.doc_concepts: Dict[int, List[Tuple[str, float]]] = {}

    def add_document(
        self,
        doc_id: int,
        work_id: str,
        text: str,
        concepts: List[Tuple[str, float]] | None = None,
    ) -> None:

        # 🔥 Apply synonym expansion
        text = normalize_text(text)

        # 🔥 Improved tokenization
        tokens = tokenize(text)
        counts = Counter(tokens)

        self.doc_ids[doc_id] = work_id
        self.doc_len[doc_id] = len(tokens)
        self.N += 1

        for term, tf in counts.items():
            self.df[term] += 1
            self.inverted[term].append((doc_id, tf))

        self.doc_concepts[doc_id] = concepts or []

    def finalize(self) -> None:
        if self.N > 0:
            self.avg_len = sum(self.doc_len.values()) / self.N

    def score(self, query: str, top_k: int = 20) -> List[Tuple[str, float]]:

        # 🔥 Normalize query too
        query = normalize_text(query)
        q_tokens = tokenize(query)

        scores: Counter = Counter()

        for term in q_tokens:
            if term not in self.inverted:
                continue

            df = self.df[term]
            idf = math.log(1 + (self.N - df + 0.5) / (df + 0.5))

            for doc_id, tf in self.inverted[term]:
                dl = self.doc_len[doc_id]
                denom = tf + self.k1 * (1 - self.b + self.b * dl / self.avg_len)
                scores[doc_id] += idf * (tf * (self.k1 + 1) / denom)

        top = scores.most_common(top_k)
        return [(self.doc_ids[doc_id], score) for doc_id, score in top]

    def get_doc_concepts(self, work_id: str) -> List[Tuple[str, float]]:
        for doc_id, wid in self.doc_ids.items():
            if wid == work_id:
                return self.doc_concepts.get(doc_id, [])
        return []
