from __future__ import annotations
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple
import bibtexparser
from .utils import (
    make_internal_doi,
    canonicalise_doi,
    make_synthetic_id
)
from .bundle_generator import lookup_crossref_metadata,lookup_openalex_metadata
from .bundle_generator import OpenAlexIngestionBundle


# ------------------------------------------------------------
# 1. Load BibTeX
# ------------------------------------------------------------

def load_bibtex(path: Path) -> List[Dict]:
    with path.open("r", encoding="utf-8") as f:
        db = bibtexparser.load(f)
    return db.entries


# ------------------------------------------------------------
# 2. Extract fields from a BibTeX entry
# ------------------------------------------------------------

def extract_bib_fields(entry: Dict) -> Dict:
    title = entry.get("title")
    authors_raw = entry.get("author", "")
    authors = [a.strip() for a in authors_raw.split(" and ")] if authors_raw else []
    year = entry.get("year")
    doi = canonicalise_doi(entry.get("doi"))
    arxiv = entry.get("eprint") if entry.get("archiveprefix") == "arXiv" else None

    return {
        "title": title,
        "authors": authors,
        "year": year,
        "doi": doi,
        "arxiv": arxiv,
        "raw": entry,
    }


# ------------------------------------------------------------
# 3. Resolve work_id (DOI → arXiv → metadata DOI → synthetic)
# ------------------------------------------------------------

def resolve_work_id(title: str, authors: List[str], year: str,
                    doi: Optional[str], arxiv: Optional[str]) -> str:

    if doi:
        return f"doi:{doi}"

    if arxiv:
        return f"arxiv:{arxiv}"

    if title and authors and year:
        return make_internal_doi(title, authors, year)

    return make_synthetic_id(title, authors, year)


# ------------------------------------------------------------
# 4. Build a bundle from a single BibTeX entry
# ------------------------------------------------------------

def build_bundle_from_bib_entry(entry: Dict) -> OpenAlexIngestionBundle:
    errors = []
    query_metadata = {
        "bibtex": {},
        "crossref": {},
        "openalex": {},
    }

    # Extract fields
    fields = extract_bib_fields(entry)
    title = fields["title"]
    authors = fields["authors"]
    year = fields["year"]
    doi = fields["doi"]
    arxiv = fields["arxiv"]

    query_metadata["bibtex"] = fields

    # Resolve work_id
    work_id = resolve_work_id(title, authors, year, doi, arxiv)

    # Crossref + OpenAlex lookups
    if doi:
        cr_meta, cr_err = lookup_crossref_metadata(doi)
        oa_meta, oa_err = lookup_openalex_metadata(doi)

        query_metadata["crossref"] = cr_meta
        query_metadata["openalex"] = oa_meta

        errors.extend(cr_err)
        errors.extend(oa_err)

    # Assemble bundle
    bundle = OpenAlexIngestionBundle(
        work_id=work_id,
        query_metadata=query_metadata,
        retrieval_timestamp=datetime.now(timezone.utc),
        errors=errors,
    )

    return bundle


# ------------------------------------------------------------
# 5. Build bundles for an entire BibTeX file
# ------------------------------------------------------------

def build_bundles_from_bibtex(path: Path) -> List[OpenAlexIngestionBundle]:
    entries = load_bibtex(path)
    bundles = []

    for entry in entries:
        try:
            bundle = build_bundle_from_bib_entry(entry)
            bundles.append(bundle)
        except Exception as e:
            # catastrophic failure for this entry only
            bundles.append(
                OpenAlexIngestionBundle(
                    work_id=f"error:{entry.get('ID', 'unknown')}",
                    query_metadata={"bibtex": entry},
                    retrieval_timestamp=datetime.now(timezone.utc),
                    errors=[f"Failed to process entry: {e}"],
                )
            )

    return bundles
