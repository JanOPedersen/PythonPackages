# src/PaperSearch/indexing/bm25_index.py

import math
from collections import Counter, defaultdict
from typing import Dict, List, Tuple


class BM25Index:
    """
    Lightweight BM25 index with optional concept metadata per document.
    """

    def __init__(self, k1: float = 1.5, b: float = 0.75):
        self.k1 = k1
        self.b = b

        self.N = 0  # number of documents
        self.doc_len: Dict[int, int] = {}
        self.avg_len: float = 0.0

        self.df: Counter = Counter()  # term -> document frequency
        self.inverted: Dict[str, List[Tuple[int, int]]] = defaultdict(list)
        self.doc_ids: Dict[int, str] = {}  # doc_id -> work_id

        # concept metadata: doc_id -> list[(concept_id, score)]
        self.doc_concepts: Dict[int, List[Tuple[str, float]]] = {}

    def add_document(
        self,
        doc_id: int,
        work_id: str,
        text: str,
        concepts: List[Tuple[str, float]] | None = None,
    ) -> None:
        tokens = text.lower().split()
        counts = Counter(tokens)

        self.doc_ids[doc_id] = work_id
        self.doc_len[doc_id] = len(tokens)
        self.N += 1

        for term, tf in counts.items():
            self.df[term] += 1
            self.inverted[term].append((doc_id, tf))

        if concepts:
            self.doc_concepts[doc_id] = concepts
        else:
            self.doc_concepts[doc_id] = []

    def finalize(self) -> None:
        if self.N > 0:
            self.avg_len = sum(self.doc_len.values()) / self.N

    def score(self, query: str, top_k: int = 20) -> List[Tuple[str, float]]:
        q_tokens = query.lower().split()
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
        # reverse lookup: work_id -> doc_id
        for doc_id, wid in self.doc_ids.items():
            if wid == work_id:
                return self.doc_concepts.get(doc_id, [])
        return []
