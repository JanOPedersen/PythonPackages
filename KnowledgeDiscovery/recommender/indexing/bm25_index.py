from __future__ import annotations
from typing import List, Tuple, Dict
import math
import re


class BM25Index:
    """
    Minimal, clean BM25 implementation suitable for your recommender.
    """

    def __init__(self, k1: float = 1.5, b: float = 0.75):
        self.k1 = k1
        self.b = b

        # Core data structures
        self.documents: Dict[str, List[str]] = {}
        self.doc_lengths: Dict[str, int] = {}
        self.avg_doc_length: float = 0.0

        # Inverted index: term -> {doc_id: term_frequency}
        self.inverted_index: Dict[str, Dict[str, int]] = {}

        self.total_docs = 0

    # -----------------------------
    # Tokenization
    # -----------------------------
    def tokenize(self, text: str) -> List[str]:
        return re.findall(r"\b\w+\b", text.lower())

    # -----------------------------
    # Adding documents
    # -----------------------------
    def add(self, doc_id: str, text: str) -> None:
        tokens = self.tokenize(text)
        self.documents[doc_id] = tokens
        self.doc_lengths[doc_id] = len(tokens)
        self.total_docs += 1

        # Update inverted index
        for tok in tokens:
            if tok not in self.inverted_index:
                self.inverted_index[tok] = {}
            self.inverted_index[tok].setdefault(doc_id, 0)
            self.inverted_index[tok][doc_id] += 1

        # Update average length
        self.avg_doc_length = sum(self.doc_lengths.values()) / self.total_docs

    # -----------------------------
    # BM25 scoring
    # -----------------------------
    def _idf(self, term: str) -> float:
        df = len(self.inverted_index.get(term, {}))
        if df == 0:
            return 0.0
        return math.log(1 + (self.total_docs - df + 0.5) / (df + 0.5))

    def _score_term(self, term: str, doc_id: str) -> float:
        tf = self.inverted_index.get(term, {}).get(doc_id, 0)
        if tf == 0:
            return 0.0

        dl = self.doc_lengths[doc_id]
        idf = self._idf(term)

        numerator = tf * (self.k1 + 1)
        denominator = tf + self.k1 * (1 - self.b + self.b * dl / self.avg_doc_length)

        return idf * (numerator / denominator)

    # -----------------------------
    # Searching
    # -----------------------------
    def search(self, query: str, k: int = 20) -> List[Tuple[str, float]]:
        tokens = self.tokenize(query)
        scores: Dict[str, float] = {}

        for term in tokens:
            postings = self.inverted_index.get(term, {})
            for doc_id in postings:
                scores.setdefault(doc_id, 0.0)
                scores[doc_id] += self._score_term(term, doc_id)

        # Sort by score
        ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        return ranked[:k]
 