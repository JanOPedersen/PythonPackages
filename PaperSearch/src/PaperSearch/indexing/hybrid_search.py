# hybrid_search.py

from PaperSearch.src.PaperSearch.sql.db.connection import get_db

class HybridSearch:
    def __init__(self, bm25, emb_index, db_path: str):
        self.bm25 = bm25
        self.emb = emb_index
        self.db_path = db_path

    def get_title(self, work_id: str) -> str:
        with get_db(self.db_path) as conn:
            row = conn.execute(
                "SELECT title FROM normalized_works WHERE work_id = ?",
                (work_id,)
            ).fetchone()
        return row["title"] if row else ""

    def search(self, query, top_k=20, alpha=1.0, boosted_concepts=None):
        bm25_results = self.bm25.score(query, top_k=300)
        q_vec = self.emb.encode(query)

        reranked = []
        for work_id, bm25_score in bm25_results:
            d_vec = self.emb.get(work_id)
            if d_vec is None:
                continue

            emb_score = self.emb.cosine_similarity(q_vec, d_vec)

            concept_boost = 1.0
            if boosted_concepts:
                doc_concepts = self.bm25.get_doc_concepts(work_id)
                for cid, score in doc_concepts:
                    if cid in boosted_concepts:
                        concept_boost += score

            final_score = bm25_score + alpha * emb_score + concept_boost
            title = self.get_title(work_id)

            reranked.append(
                (work_id, title, final_score, bm25_score, emb_score, concept_boost)
            )

        reranked.sort(key=lambda x: x[2], reverse=True)
        return reranked[:top_k]
