"""
Bibliographic metadata normalization and cleanup.

This module provides pure functions that operate on the Document model:
- title normalization
- author normalization
- identifier normalization
- year extraction
- venue inference (optional)
"""

from __future__ import annotations
from typing import Optional
from representation.core.core_entities import (
    Document,
    Person,
    Identifier,
    Venue,
)


# ------------------------------------------------------------
# Helpers
# ------------------------------------------------------------

def _clean(text: Optional[str]) -> Optional[str]:
    if text is None:
        return None
    t = text.strip()
    return t if t else None


# ------------------------------------------------------------
# Title normalization
# ------------------------------------------------------------

def normalize_title(doc: Document) -> Document:
    if doc.title:
        doc.title = _clean(doc.title)
        # Remove trailing periods (common in arXiv titles)
        if doc.title and doc.title.endswith("."):
            doc.title = doc.title[:-1]
    return doc


# ------------------------------------------------------------
# Author normalization
# ------------------------------------------------------------

def normalize_authors(doc: Document) -> Document:
    if not doc.authors:
        return doc

    normalized = []
    for person in doc.authors:
        given = _clean(person.given)
        family = _clean(person.family)

        # If arXiv gave "John Doe" as family name only
        if given is None and family and " " in family:
            parts = family.split(" ", 1)
            given = parts[0]
            family = parts[1]

        normalized.append(
            Person(
                given=given,
                family=family,
                orcid=person.orcid,
                affiliation=person.affiliation,
            )
        )

    doc.authors = normalized
    return doc


# ------------------------------------------------------------
# Identifier normalization
# ------------------------------------------------------------

def normalize_identifiers(doc: Document) -> Document:
    seen = set()
    unique = []

    for ident in doc.identifiers:
        key = (ident.type, ident.value)
        if key not in seen:
            seen.add(key)
            unique.append(ident)

    doc.identifiers = unique
    return doc


# ------------------------------------------------------------
# Year extraction
# ------------------------------------------------------------

def infer_year_from_identifiers(doc: Document) -> Document:
    """
    If year is missing, try to infer from arXiv ID or DOI.
    Example arXiv ID: 2101.12345 → year 2021
    """
    if doc.year is not None:
        return doc

    for ident in doc.identifiers:
        if ident.type == "arxiv":
            raw = ident.value.replace("arXiv:", "")
            if len(raw) >= 2 and raw[:2].isdigit():
                year = int("20" + raw[:2])
                doc.year = year
                return doc

    return doc


# ------------------------------------------------------------
# Venue inference
# ------------------------------------------------------------

def infer_venue(doc: Document) -> Document:
    if doc.venue is not None:
        return doc

    # Simple rule: arXiv → repository
    if any(i.type == "arxiv" for i in doc.identifiers):
        doc.venue = Venue(name="arXiv", type="repository")

    return doc


# ------------------------------------------------------------
# Pipeline
# ------------------------------------------------------------

def process_bibliographic(doc: Document) -> Document:
    doc = normalize_title(doc)
    doc = normalize_authors(doc)
    doc = normalize_identifiers(doc)
    doc = infer_year_from_identifiers(doc)
    doc = infer_venue(doc)
    return doc
 