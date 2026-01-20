"""
Content-level metadata extraction and normalization.

This module provides pure functions that operate on the Document model:
- abstract cleanup
- keyword extraction (simple heuristic)
- language detection (optional, lightweight)
"""

from __future__ import annotations
from typing import List, Optional
from representation.core.core_entities import Document


# ------------------------------------------------------------
# Helpers
# ------------------------------------------------------------

def _clean(text: Optional[str]) -> Optional[str]:
    if text is None:
        return None
    t = text.strip()
    return t if t else None


# ------------------------------------------------------------
# Abstract cleanup
# ------------------------------------------------------------

def clean_abstract(doc: Document) -> Document:
    if doc.abstract:
        doc.abstract = _clean(doc.abstract)
    return doc


# ------------------------------------------------------------
# Keyword extraction (simple heuristic)
# ------------------------------------------------------------

def extract_keywords(doc: Document, max_keywords: int = 10) -> List[str]:
    """
    Very simple keyword extractor:
    - split on whitespace
    - lowercase
    - remove stopwords
    - remove very short tokens
    - return top-N unique tokens in order of appearance
    """

    if not doc.abstract:
        return []

    text = doc.abstract.lower()

    stopwords = {
        "the", "and", "or", "of", "in", "on", "for", "to", "a", "an", "with",
        "this", "that", "these", "those", "we", "our", "is", "are", "be",
    }

    tokens = [t.strip(".,;:()[]") for t in text.split()]
    keywords = []

    for token in tokens:
        if len(token) < 3:
            continue
        if token in stopwords:
            continue
        if token not in keywords:
            keywords.append(token)
        if len(keywords) >= max_keywords:
            break

    return keywords


# ------------------------------------------------------------
# Language detection (very lightweight heuristic)
# ------------------------------------------------------------

def detect_language(doc: Document) -> Optional[str]:
    """
    Extremely lightweight heuristic:
    - If abstract contains common English words → 'en'
    - Otherwise return None
    """

    if not doc.abstract:
        return None

    english_markers = {"the", "and", "this", "that", "we", "our", "paper"}

    text = doc.abstract.lower()
    if any(word in text for word in english_markers):
        return "en"

    return None


# ------------------------------------------------------------
# Pipeline
# ------------------------------------------------------------

def process_content(doc: Document) -> Document:
    doc = clean_abstract(doc)
    # Keyword extraction and language detection do not mutate the Document
    # but you may later store them in doc.metadata or doc.enrichment
    return doc
 