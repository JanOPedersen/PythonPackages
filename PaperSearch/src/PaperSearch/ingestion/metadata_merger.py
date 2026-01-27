from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional, Dict, List

# --- your imports ---
from PaperSearch.ingestion.grobid_client import grobid_search_pdf
from PaperSearch.ingestion.utils import (
    canonicalise_doi,
    make_internal_doi,
    make_pdf_hash_doi,
)
from PaperSearch.ingestion.crossref_client import crossref_search_doi, crossref_search_title
from PaperSearch.ingestion.openalex_client import (
    openalex_search_doi,
    openalex_search_arxiv,
    openalex_search_title,
    openalex_get_work,
    openalex_get_related,
)

@dataclass
class OpenAlexIngestionBundle:
    work_id: str
    work: dict | None
    authorships: dict | None
    related_works: dict | None
    query_metadata: dict
    retrieval_timestamp: datetime
    errors: list[str]


def build_bundle_from_pdf(pdf_path: str) -> OpenAlexIngestionBundle:
    errors = []
    query_metadata = {
        "pdf": {},
        "crossref": {},
        "openalex": {},
    }

    # ------------------------------------------------------------
    # 1. Extract metadata from PDF via GROBID
    # ------------------------------------------------------------
    try:
        tei = grobid_search_pdf(pdf_path)
        pdf_title = tei.get("title")
        pdf_authors = tei.get("authors", [])
        pdf_year = tei.get("year")
        pdf_doi = canonicalise_doi(tei.get("doi"))
        pdf_arxiv = tei.get("arxiv_id")
    except Exception as e:
        errors.append(f"GROBID extraction failed: {e}")
        tei = {}
        pdf_title = pdf_authors = pdf_year = pdf_doi = pdf_arxiv = None

    query_metadata["pdf"] = {
        "path": pdf_path,
        "title": pdf_title,
        "authors": pdf_authors,
        "year": pdf_year,
        "doi": pdf_doi,
        "arxiv": pdf_arxiv,
    }

    # ------------------------------------------------------------
    # 2. Resolve work_id (priority: DOI → arXiv → metadata DOI → PDF hash)
    # ------------------------------------------------------------
    work_id = None

    # A. Real DOI from PDF
    if pdf_doi:
        work_id = f"doi:{pdf_doi}"

    # B. arXiv ID
    elif pdf_arxiv:
        work_id = f"arxiv:{pdf_arxiv}"

    # C. Deterministic internal DOI (title + authors + year)
    elif pdf_title and pdf_authors and pdf_year:
        work_id = make_internal_doi(pdf_title, pdf_authors, pdf_year)

    # D. PDF-hash DOI fallback
    else:
        work_id = make_pdf_hash_doi(pdf_path)

    # ------------------------------------------------------------
    # 3. Crossref lookup (if DOI available)
    # ------------------------------------------------------------
    crossref_data = None
    if pdf_doi:
        try:
            crossref_data = crossref_search_doi(pdf_doi)
            query_metadata["crossref"]["doi_query"] = pdf_doi
            query_metadata["crossref"]["result"] = bool(crossref_data)
        except Exception as e:
            errors.append(f"Crossref lookup failed: {e}")
            query_metadata["crossref"]["error"] = str(e)

    # ------------------------------------------------------------
    # 4. OpenAlex lookup
    # ------------------------------------------------------------
    openalex_work = None
    openalex_authorships = None
    openalex_related = None

    try:
        # A. Try DOI
        if pdf_doi:
            openalex_work = openalex_search_doi(pdf_doi)

        # B. Try arXiv
        if not openalex_work and pdf_arxiv:
            openalex_work = openalex_search_arxiv(pdf_arxiv)

        # C. Try title search
        if not openalex_work and pdf_title:
            openalex_work = openalex_search_title(pdf_title)

        # If we found an OpenAlex work, fetch details
        if openalex_work and "id" in openalex_work:
            openalex_id = openalex_work["id"]
            query_metadata["openalex"]["resolved_id"] = openalex_id

            # Fetch full work
            openalex_work = openalex_get_work(openalex_id)

            # Extract authorships
            openalex_authorships = openalex_work.get("authorships")

            # Fetch related works
            openalex_related = openalex_get_related(openalex_id)

    except Exception as e:
        errors.append(f"OpenAlex lookup failed: {e}")
        query_metadata["openalex"]["error"] = str(e)

    # ------------------------------------------------------------
    # 5. Assemble bundle
    # ------------------------------------------------------------
    bundle = OpenAlexIngestionBundle(
        work_id=work_id,
        work=openalex_work,
        authorships=openalex_authorships,
        related_works=openalex_related,
        query_metadata=query_metadata,
        retrieval_timestamp = datetime.now(timezone.utc),
        errors=errors,
    )

    return bundle
