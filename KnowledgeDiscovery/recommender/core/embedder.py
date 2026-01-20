from __future__ import annotations
import numpy as np
from sentence_transformers import SentenceTransformer


class SentenceTransformerEmbedder:
    """
    Thin wrapper around a SentenceTransformer model.
    Produces L2-normalized embeddings for stability.
    """

    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
        self.model = SentenceTransformer(model_name)

    def __call__(self, text: str) -> np.ndarray:
        emb = self.model.encode(text, convert_to_numpy=True)
        # Normalize for cosine similarity stability
        norm = np.linalg.norm(emb)
        return emb / norm if norm > 0 else emb
