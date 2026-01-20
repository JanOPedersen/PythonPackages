from __future__ import annotations
import re
from typing import List
from representation.core.core_entities import Document

# ------------------------------------------------------------
# Domain stopwords (scientific abstracts)
# ------------------------------------------------------------

SCIENTIFIC_STOPWORDS = {
    # generic English
    "the", "and", "or", "of", "in", "on", "for", "to", "a", "an", "with",
    "this", "that", "these", "those", "we", "our", "is", "are", "be",

    # scientific boilerplate
    "paper", "study", "approach", "method", "methods", "results",
    "introduce", "introduces", "propose", "proposed", "present", "presents",
    "show", "shows", "demonstrate", "demonstrates",
}

# ------------------------------------------------------------
# Keyword extraction (enrichment-level)
# ------------------------------------------------------------

def extract_keywords_enriched(
    doc: Document,
    max_keywords: int = 15,
    stopwords: set[str] = SCIENTIFIC_STOPWORDS,
) -> List[str]:
    """
    Improved keyword extractor for enrichment:
    - regex tokenization
    - lowercase normalization
    - domain stopwords
    - deduplication with order preserved
    """

    if not doc.abstract:
        return []

    text = doc.abstract.lower()

    # Extract alphabetic tokens only
    tokens = re.findall(r"[a-z]+", text)

    keywords: List[str] = []
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
# Enrichment wrapper
# ------------------------------------------------------------

def enrich_keywords(doc: Document) -> Document:
    """
    Attach extracted keywords to doc.enrichment.
    """
    kws = extract_keywords_enriched(doc)

    if not hasattr(doc, "enrichment") or doc.enrichment is None:
        doc.enrichment = {}

    doc.enrichment["keywords"] = kws
    return doc
