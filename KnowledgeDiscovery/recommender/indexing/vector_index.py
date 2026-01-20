from __future__ import annotations
from typing import Dict, List, Tuple
import numpy as np


class VectorIndex:
    """
    Minimal vector index for semantic search.
    Stores L2-normalized embeddings and performs cosine similarity search.
    """

    def __init__(self, dim: int):
        self.dim = dim
        self.embeddings: Dict[str, np.ndarray] = {}

    # -----------------------------
    # Add document embedding
    # -----------------------------
    def add(self, doc_id: str, embedding: np.ndarray) -> None:
        if embedding.shape[0] != self.dim:
            raise ValueError(f"Embedding dimension mismatch: expected {self.dim}, got {embedding.shape[0]}")

        # Normalize for cosine similarity
        norm = np.linalg.norm(embedding)
        if norm > 0:
            embedding = embedding / norm

        self.embeddings[doc_id] = embedding

    # -----------------------------
    # Search by cosine similarity
    # -----------------------------
    def search(self, query_vec: np.ndarray, k: int = 20) -> List[Tuple[str, float]]:
        if query_vec.shape[0] != self.dim:
            raise ValueError(f"Query dimension mismatch: expected {self.dim}, got {query_vec.shape[0]}")

        # Normalize query
        q = query_vec / np.linalg.norm(query_vec) if np.linalg.norm(query_vec) > 0 else query_vec

        scores = {}
        for doc_id, emb in self.embeddings.items():
            score = float(np.dot(q, emb))  # cosine similarity
            scores[doc_id] = score

        ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        return ranked[:k]
 