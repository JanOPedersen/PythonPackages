import sqlite3
from .bm25_index import BM25Index


class CanonicalSearch:
    def __init__(self, db_path: str, bm25_index: BM25Index):
        self.db_path = db_path
        self.bm25 = bm25_index

    def search(self, query: str, top_k: int = 20):
        ranked = self.bm25.score(query, top_k=top_k)
        return [self.fetch_metadata(work_id) for work_id, _ in ranked]

    def fetch_metadata(self, work_id: str):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        row = conn.execute(
            "SELECT * FROM normalized_works WHERE work_id = ?", (work_id,)
        ).fetchone()
        conn.close()
        return dict(row) if row else None
 