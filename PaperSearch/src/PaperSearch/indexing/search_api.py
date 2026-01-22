# src/PaperSearch/indexing/search_api.py

import sqlite3
import json
from typing import List, Dict, Any

from .bm25_index import BM25Index


class CanonicalSearch:
    def __init__(self, db_path: str, bm25_index: BM25Index):
        self.db_path = db_path
        self.bm25 = bm25_index

    def _fetch_metadata_bulk(self, work_ids: List[str]) -> List[Dict[str, Any]]:
        if not work_ids:
            return []

        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row

        placeholders = ",".join("?" for _ in work_ids)
        query = f"SELECT * FROM normalized_works WHERE work_id IN ({placeholders})"
        rows = conn.execute(query, work_ids).fetchall()
        conn.close()

        by_id = {row["work_id"]: dict(row) for row in rows}
        return [by_id[wid] for wid in work_ids if wid in by_id]

    def _concept_boost(
        self,
        work_id: str,
        boosted_concepts: List[str] | None,
    ) -> float:
        if not boosted_concepts:
            return 0.0

        doc_concepts = self.bm25.get_doc_concepts(work_id)
        boosted_set = set(boosted_concepts)

        score = 0.0
        for cid, cscore in doc_concepts:
            if cid in boosted_set:
                score += cscore
        return score

    def _has_required_concepts(
        self,
        work_id: str,
        required_concepts: List[str],
    ) -> bool:
        if not required_concepts:
            return True

        doc_concepts = self.bm25.get_doc_concepts(work_id)
        doc_ids = {cid for cid, _ in doc_concepts}
        return all(rc in doc_ids for rc in required_concepts)

    def search(
        self,
        query: str,
        top_k: int = 20,
        required_concepts: List[str] | None = None,
        boosted_concepts: List[str] | None = None,
        alpha: float = 1.0,
    ) -> List[Dict[str, Any]]:
        """
        Minimal unified API:
        - BM25 lexical ranking
        - optional hard concept filtering
        - optional soft concept boosting (weight alpha)
        """

        # 1. BM25 lexical ranking (get more than top_k to allow filtering)
        bm25_hits = self.bm25.score(query, top_k=max(top_k * 5, top_k))
        # bm25_hits: list[(work_id, bm25_score)]

        # 2. Apply hard concept filtering at the ID level
        filtered_hits: list[tuple[str, float]] = []
        for work_id, score in bm25_hits:
            if self._has_required_concepts(work_id, required_concepts or []):
                filtered_hits.append((work_id, score))

        if not filtered_hits:
            return []

        # 3. Fetch metadata for remaining candidates
        work_ids = [wid for wid, _ in filtered_hits]
        docs = self._fetch_metadata_bulk(work_ids)

        # index by work_id for attaching scores
        score_by_id = {wid: s for wid, s in filtered_hits}

        # 4. Attach scores and compute final_score
        enriched: list[dict[str, Any]] = []
        for d in docs:
            wid = d["work_id"]
            bm25_score = score_by_id.get(wid, 0.0)
            concept_boost = self._concept_boost(wid, boosted_concepts or [])

            final_score = bm25_score + alpha * concept_boost

            d = dict(d)
            d["bm25_score"] = bm25_score
            d["concept_boost"] = concept_boost
            d["final_score"] = final_score
            enriched.append(d)

        # 5. Sort and return top_k
        enriched.sort(key=lambda x: x["final_score"], reverse=True)
        return enriched[:top_k]
