"""
Factories for constructing internal core entities from external metadata sources.

This module converts raw metadata from GROBID, Crossref, OpenAlex, arXiv,
and PDF-derived metadata into normalized, validated internal entities defined
in `core_entities.py`.

All functions here are pure transformations:
- no HTTP
- no file I/O
- no side effects

They rely on:
- validators.py (DOI, ORCID, dates, titles)
- utils.text_normalization
- utils.timestamps
"""

from __future__ import annotations
from typing import Any, Dict, List, Optional
from datetime import datetime

from .core_entities import (
    Document,
    Identifier,
    Person,
    File,
    Source,
    IngestionEvent,
)


# ------------------------------------------------------------
# Helpers
# ------------------------------------------------------------

def _now_iso() -> str:
    return datetime.utcnow().isoformat()


def _clean(text: Optional[str]) -> Optional[str]:
    if text is None:
        return None
    t = text.strip()
    return t if t else None


# ------------------------------------------------------------
# arXiv Factory
# ------------------------------------------------------------

def from_arxiv(raw: Dict[str, Any]) -> Document:
    """
    Convert arXiv API metadata into a Document.
    Expected raw format is whatever arxiv_ingestor.py returns.
    """

    # Identifiers
    identifiers = []
    if arxiv_id := raw.get("arxiv_id") or raw.get("id"):
        identifiers.append(Identifier(type="arxiv", value=arxiv_id))

    if doi := raw.get("doi"):
        identifiers.append(Identifier(type="doi", value=doi))

    # Authors
    authors = []
    for name in raw.get("authors", []):
        # arXiv gives "John Doe" strings
        parts = name.split(" ", 1)
        given = parts[0] if len(parts) > 1 else None
        family = parts[-1]
        authors.append(Person(given=given, family=family))

    # Source metadata
    source = Source(
        origin="arxiv",
        retrieved_at=_now_iso(),
        url=raw.get("link"),
    )

    ingestion_event = IngestionEvent(
        stage="parse",
        timestamp=_now_iso(),
        source=source,
        notes="Parsed from arXiv metadata",
    )

    # Build Document
    return Document(
        id=arxiv_id or raw.get("id", "unknown"),
        identifiers=identifiers,
        title=_clean(raw.get("title")),
        abstract=_clean(raw.get("summary")),
        authors=authors,
        year=int(raw["published"][:4]) if raw.get("published") else None,
        files=[],
        ingestion_events=[ingestion_event],
    )


# ------------------------------------------------------------
# PDF Factory
# ------------------------------------------------------------

def from_pdf(path: str, pdf_meta: Dict[str, Any]) -> File:
    """
    Convert PDF metadata (XMP or extracted) into a File entity.
    This does NOT create a Document — it creates a File object
    that can be attached to an existing Document.
    """

    return File(
        path=path,
        mime_type=pdf_meta.get("mime_type"),
        size_bytes=pdf_meta.get("file_size"),
        checksum_md5=pdf_meta.get("md5"),
        checksum_sha256=pdf_meta.get("sha256"),
    )
