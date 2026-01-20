from __future__ import annotations
from typing import Dict, List, Tuple, Optional

from ..core.query import QueryRepresentation
from KnowledgeDiscovery.representation.core.core_entities import Document
from ..indexing.bm25_index import BM25Index
from ..indexing.vector_index import VectorIndex


class HybridRecommender:
    """
    Hybrid recommender that combines BM25 (lexical) and vector (semantic) scores.
    """

    def __init__(
        self,
        text_index: BM25Index,
        vector_index: VectorIndex,
        documents: Dict[str, Document],
        w_text: float = 0.6,
        w_sem: float = 0.4,
    ):
        self.text_index = text_index
        self.vector_index = vector_index
        self.documents = documents
        self.w_text = w_text
        self.w_sem = w_sem

    # -----------------------------
    # Score normalization helpers
    # -----------------------------
    def _normalize_scores(self, scores: Dict[str, float]) -> Dict[str, float]:
        if not scores:
            return {}
        values = list(scores.values())
        min_s, max_s = min(values), max(values)
        if max_s == min_s:
            return {k: 1.0 for k in scores}  # all equal
        return {k: (v - min_s) / (max_s - min_s) for k, v in scores.items()}

    # -----------------------------
    # Main recommend method
    # -----------------------------
    def recommend(
        self,
        query: QueryRepresentation,
        k: int = 10,
        apply_constraints: bool = True,
    ) -> List[Tuple[Document, float]]:
        # 1. Retrieve candidates from both indices
        text_hits = self.text_index.search(query.raw_text, k=5 * k)
        vec_hits: List[Tuple[str, float]] = []
        if query.embedding is not None:
            vec_hits = self.vector_index.search(query.embedding, k=5 * k)

        # 2. Convert to dicts for easier fusion
        text_scores = {doc_id: score for doc_id, score in text_hits}
        vec_scores = {doc_id: score for doc_id, score in vec_hits}

        # 3. Normalize scores to [0, 1]
        text_norm = self._normalize_scores(text_scores)
        vec_norm = self._normalize_scores(vec_scores)

        # 4. Fuse scores
        fused: Dict[str, float] = {}
        all_doc_ids = set(text_norm.keys()) | set(vec_norm.keys())
        for doc_id in all_doc_ids:
            s_text = text_norm.get(doc_id, 0.0)
            s_sem = vec_norm.get(doc_id, 0.0)
            fused[doc_id] = self.w_text * s_text + self.w_sem * s_sem

        # 5. Apply constraints (stub for now)
        if apply_constraints and query.constraints:
            fused = self._apply_constraints(fused, query.constraints)

        # 6. Rank and return top-k
        ranked = sorted(fused.items(), key=lambda x: x[1], reverse=True)
        results: List[Tuple[Document, float]] = []
        for doc_id, score in ranked[:k]:
            doc = self.documents.get(doc_id)
            if doc is not None:
                results.append((doc, score))

        return results

    # -----------------------------
    # Constraint handling (stub)
    # -----------------------------
    def _apply_constraints(
        self,
        scores: Dict[str, float],
        constraints: Dict[str, object],
    ) -> Dict[str, float]:
        # Placeholder: later you can filter/boost based on year, venue, tags, etc.
        # For now, just return scores unchanged.
        return scores
