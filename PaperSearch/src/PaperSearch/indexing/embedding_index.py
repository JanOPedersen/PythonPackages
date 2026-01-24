# embedding_index.py

import sqlite3
import numpy as np
from sentence_transformers import SentenceTransformer

class EmbeddingIndex:
    def __init__(self, db_path: str, model_name: str = "sentence-transformers/all-mpnet-base-v2"):
        self.db_path = db_path
        self.model = SentenceTransformer(model_name)

        with sqlite3.connect(db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS embeddings (
                    work_id TEXT PRIMARY KEY,
                    vector BLOB
                )
            """)

    def encode(self, text: str) -> np.ndarray:
        return self.model.encode(text, convert_to_numpy=True)

    def add(self, work_id: str, text: str):
        vec = self.encode(text)
        blob = vec.tobytes()

        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "REPLACE INTO embeddings (work_id, vector) VALUES (?, ?)",
                (work_id, blob)
            )

    def get(self, work_id: str) -> np.ndarray | None:
        with sqlite3.connect(self.db_path) as conn:
            row = conn.execute("SELECT vector FROM embeddings WHERE work_id = ?", (work_id,)).fetchone()
        if not row:
            return None
        return np.frombuffer(row[0], dtype=np.float32)

    def cosine_similarity(self, q_vec: np.ndarray, d_vec: np.ndarray) -> float:
        return float(np.dot(q_vec, d_vec) / (np.linalg.norm(q_vec) * np.linalg.norm(d_vec)))
