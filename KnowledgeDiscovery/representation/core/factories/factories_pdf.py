from __future__ import annotations
from ..core_entities import Document
from .grobid_client import GrobidClient
from .grobid_tei_parser import parse_tei
from .doi_pipeline import extract_doi
from lxml import etree
from .factories_crossref import from_doi as crossref_from_doi
from .factories_openalex import from_doi as openalex_from_doi
from .merge_metadata import merge_metadata
from datetime import datetime
from ..core_entities import (
    Document, Person, Venue, File, Source, IngestionEvent
)
import requests
import difflib
from typing import Optional, List, Dict


# ------------------------------------------------------------
# Helpers
# ------------------------------------------------------------

def normalize_title(title: str) -> str:
    """Normalize titles for comparison."""
    return (
        title.lower()
        .replace("–", "-")
        .replace("—", "-")
        .replace(":", "")
        .replace(",", "")
        .strip()
    )


def title_similarity(a: str, b: str) -> float:
    """Compute fuzzy similarity between two titles."""
    return difflib.SequenceMatcher(None, normalize_title(a), normalize_title(b)).ratio()


# ------------------------------------------------------------
# Crossref search
# ------------------------------------------------------------

def search_crossref(title: str) -> Optional[str]:
    """Search Crossref by title and return DOI if confident."""
    url = "https://api.crossref.org/works"
    params = {
        "query.title": title,
        "rows": 5,
        "select": "title,DOI,author,issued",
    }

    try:
        r = requests.get(url, params=params, timeout=10)
        r.raise_for_status()
        items = r.json().get("message", {}).get("items", [])
    except Exception:
        return None

    if not items:
        return None

    # Pick best match by title similarity
    best = None
    best_score = 0

    for item in items:
        cr_title = item.get("title", [""])[0]
        score = title_similarity(title, cr_title)

        if score > best_score:
            best_score = score
            best = item

    # Require a strong match
    if best and best_score >= 0.75:
        return best.get("DOI")

    return None


# ------------------------------------------------------------
# OpenAlex search
# ------------------------------------------------------------

def search_openalex(title: str) -> Optional[str]:
    """Search OpenAlex by title and return DOI if confident."""
    url = "https://api.openalex.org/works"
    params = {
        "search": f'title:"{title}"',
        "per-page": 5,
    }

    try:
        r = requests.get(url, params=params, timeout=10)
        r.raise_for_status()
        items = r.json().get("results", [])
    except Exception:
        return None

    if not items:
        return None

    best = None
    best_score = 0

    for item in items:
        oa_title = item.get("title", "")
        score = title_similarity(title, oa_title)

        if score > best_score:
            best_score = score
            best = item

    if best and best_score >= 0.75:
        doi = best.get("doi")
        if doi:
            return doi.replace("https://doi.org/", "")

    return None


# ------------------------------------------------------------
# Main function
# ------------------------------------------------------------

def infer_doi(title: str, authors: List[Dict] = None, year: int = None) -> Optional[str]:
    """
    Infer DOI using:
        1. Crossref title search
        2. OpenAlex title search
    """
    if not title:
        return None

    # 1. Try Crossref
    doi = search_crossref(title)
    if doi:
        return doi

    # 2. Try OpenAlex
    doi = search_openalex(title)
    if doi:
        return doi

    return None


def normalize_references(refs):
    """Ensure references are always dicts, never raw strings."""
    out = []
    for r in refs or []:
        if isinstance(r, str):
            out.append({"id": r})
        elif isinstance(r, dict):
            out.append(r)
        else:
            out.append({"id": str(r)})
    return out


def from_pdf(pdf_path: str, grobid=None) -> Document:
    grobid = grobid or GrobidClient()

    # 1. GROBID
    tei_header = grobid.process_header(pdf_path)
    tei_fulltext = grobid.process_fulltext(pdf_path)

    print("tei_header: ", )
    print(tei_header)
    print("tei_fulltext: ", )
    print(tei_fulltext)

    fulltext_meta = parse_tei(tei_fulltext)
    header_meta = parse_tei(tei_header)

    # header wins
    grobid_meta = {**fulltext_meta, **header_meta}

    root = etree.fromstring(tei_header.encode("utf-8"))

    # 2. DOI from PDF or TEI
    doi = extract_doi(pdf_path, tei_root=root)

    # 2b. DOI inference (FIXED: use grobid_meta, not merged)
    if not doi:
        doi = infer_doi(
            grobid_meta.get("title"),
            grobid_meta.get("authors"),
            grobid_meta.get("year")
        )

    # 3. Crossref
    crossref_meta = crossref_from_doi(doi) if doi else None

    # 4. OpenAlex
    openalex_meta = openalex_from_doi(doi) if doi else None

    # 5. Merge metadata
    merged = merge_metadata(grobid_meta, crossref_meta, openalex_meta)

    # 6. Convert authors
    authors = []
    for a in merged.get("authors", []):
        # skip affiliation-only pseudo-authors
        if not a.get("given") and not a.get("family"):
            continue

        authors.append(
            Person(
                given=a.get("given"),
                family=a.get("family"),
                orcid=a.get("orcid") if isinstance(a.get("orcid"), str) else None,
                affiliation=a.get("affiliation") if isinstance(a.get("affiliation"), str) else None
            )
        )

    # 7. Venue
    venue = None
    if merged.get("venue"):
        venue = Venue(
            name=merged["venue"],
            type="journal"
        )

    # 8. Files
    files = [File(path=pdf_path)]

    # 9. Ingestion event
    ingestion_events = [
        IngestionEvent(
            stage="extract",
            timestamp=datetime.utcnow().isoformat(),
            source=Source(
                name="grobid",
                origin="grobid"
            )
        )
    ]

    # 10. Normalize references
    references = normalize_references(merged.get("references"))

    # 11. Build Document
    return Document(
        id=doi or f"pdf:{pdf_path}",
        identifiers=[{"type": "doi", "value": doi}] if doi else [],
        title=merged.get("title"),
        abstract=merged.get("abstract"),
        authors=authors,
        venue=venue,
        year=merged.get("year"),
        references=references,
        files=files,
        ingestion_events=ingestion_events,
    )
