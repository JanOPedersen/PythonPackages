import math
from collections import Counter, defaultdict


class BM25Index:
    """
    A lightweight BM25 index suitable for canonical search.
    """

    def __init__(self, k1: float = 1.5, b: float = 0.75):
        self.k1 = k1
        self.b = b

        self.N = 0  # number of indexed documents
        self.doc_len = {}  # doc_id -> length
        self.avg_len = 0.0

        self.df = Counter()  # term -> document frequency
        self.inverted = defaultdict(list)  # term -> list[(doc_id, tf)]
        self.doc_ids = {}  # doc_id -> work_id

    def add_document(self, doc_id: int, work_id: str, text: str):
        tokens = text.lower().split()
        counts = Counter(tokens)

        self.doc_ids[doc_id] = work_id
        self.doc_len[doc_id] = len(tokens)
        self.N += 1

        for term, tf in counts.items():
            self.df[term] += 1
            self.inverted[term].append((doc_id, tf))

    def finalize(self):
        if self.N > 0:
            self.avg_len = sum(self.doc_len.values()) / self.N

    def score(self, query: str, top_k: int = 20):
        q_tokens = query.lower().split()
        scores = Counter()

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
