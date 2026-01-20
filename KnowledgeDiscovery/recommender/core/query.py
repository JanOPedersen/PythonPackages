from __future__ import annotations
from dataclasses import dataclass
from typing import List, Optional, Dict
import numpy as np
import re


# ---------------------------------------------------------
# Query Representation
# ---------------------------------------------------------

@dataclass(frozen=True)
class QueryRepresentation:
    """
    Immutable representation of a user query.
    This is the object consumed by the recommender.
    """
    raw_text: str
    tokens: List[str]
    embedding: np.ndarray
    constraints: Optional[Dict[str, object]] = None


# ---------------------------------------------------------
# Query Parser
# ---------------------------------------------------------

class QueryParser:
    """
    Minimal, extensible parser that converts raw text into a QueryRepresentation.
    """

    def __init__(self, embedder=None):
        """
        embedder: callable that takes text -> np.ndarray
        If None, a zero-vector placeholder is used.
        """
        self.embedder = embedder

    # -----------------------------
    # Tokenization
    # -----------------------------
    def tokenize(self, text: str) -> List[str]:
        return re.findall(r"\b\w+\b", text.lower())

    # -----------------------------
    # Constraint extraction (minimal stub)
    # -----------------------------
    def extract_constraints(self, text: str) -> Dict[str, object]:
        """
        Placeholder for future constraint parsing.
        For now, returns an empty dict.
        """
        return {}

    # -----------------------------
    # Embedding generation
    # -----------------------------
    def embed(self, text: str) -> np.ndarray:
        if self.embedder is None:
            return np.zeros(384, dtype=float)
        return self.embedder(text)

    # -----------------------------
    # Main entry point
    # -----------------------------
    def parse(self, text: str) -> QueryRepresentation:
        tokens = self.tokenize(text)
        embedding = self.embed(text)
        constraints = self.extract_constraints(text)

        return QueryRepresentation(
            raw_text=text,
            tokens=tokens,
            embedding=embedding,
            constraints=constraints or None
        )
