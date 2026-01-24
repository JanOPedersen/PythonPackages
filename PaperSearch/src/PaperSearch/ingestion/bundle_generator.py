from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from collections import defaultdict
from tqdm import tqdm

# --- your imports ---
from PaperSearch.src.PaperSearch.ingestion.grobid_client import grobid_search_pdf
from PaperSearch.src.PaperSearch.ingestion.utils import (
    canonicalise_doi,
    make_internal_doi,
    make_pdf_hash_doi,
)
from PaperSearch.src.PaperSearch.ingestion.crossref_client import crossref_search_doi, crossref_search_query
from PaperSearch.src.PaperSearch.ingestion.openalex_client import openalex_search_doi, openalex_search_query


@dataclass
class OpenAlexIngestionBundle:
    work_id: str
    query_metadata: dict
    retrieval_timestamp: datetime
    errors: list[str]

def lookup_crossref_metadata(doi: str) -> tuple[dict, list[str]]:
    metadata = {}
    errors = []
    try:
        cr = crossref_search_doi(doi)
        if cr:
            if "DOI" in cr:
                metadata["doi"] = cr["DOI"]
            if "author" in cr:
                metadata["authors"] = cr["author"]
            if "year" in cr:
                metadata["year"] = cr["year"]
            if "title" in cr:
                metadata["title"] = cr["title"]
    except Exception as e:
        errors.append(f"Crossref lookup failed: {e}")
        metadata["error"] = str(e)

    return metadata, errors


def lookup_openalex_metadata(doi: str) -> tuple[dict, list[str]]:
    metadata = {}
    errors = []
    try:
        oa = openalex_search_doi(doi)
        if oa:
            if "doi" in oa:
                metadata["doi"] = oa["doi"]
            if "authorships" in oa:
                metadata["authors"] = oa["authorships"]
            if "publication_year" in oa:
                metadata["year"] = oa["publication_year"]
            if "title" in oa:
                metadata["title"] = oa["title"]
            if "concepts" in oa: 
                metadata["concepts"] = oa["concepts"]
            if "abstract_inverted_index" in oa:
                metadata["abstract_inverted_index"] = oa["abstract_inverted_index"]
            
    except Exception as e:
        errors.append(f"OpenAlex lookup failed: {e}")
        metadata["error"] = str(e)

    return metadata, errors


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
    if pdf_doi:
        work_id = f"doi:{pdf_doi}"
    elif pdf_arxiv:
        work_id = f"arxiv:{pdf_arxiv}"
    elif pdf_title and pdf_authors and pdf_year:
        work_id = make_internal_doi(pdf_title, pdf_authors, pdf_year)
    else:
        work_id = make_pdf_hash_doi(pdf_path)

    # ------------------------------------------------------------
    # 3. CrossRef + OpenAlex lookups (refactored)
    # ------------------------------------------------------------
    if pdf_doi:
        cr_meta, cr_err = lookup_crossref_metadata(pdf_doi)
        oa_meta, oa_err = lookup_openalex_metadata(pdf_doi)

        query_metadata["crossref"] = cr_meta
        query_metadata["openalex"] = oa_meta

        errors.extend(cr_err)
        errors.extend(oa_err)

    # ------------------------------------------------------------
    # 4. Assemble bundle
    # ------------------------------------------------------------
    bundle = OpenAlexIngestionBundle(
        work_id=work_id,
        query_metadata=query_metadata,
        retrieval_timestamp=datetime.now(timezone.utc),
        errors=errors,
    )

    return bundle


# ------------------------------------------------------------
# Helper: find a local PDF matching a DOI
# TODO: customize this, so that it reads from a database or uses a different matching logic
# ------------------------------------------------------------
def find_pdf_for_doi(doi: str, roots: list[str]) -> str | None:
    """
    Search recursively under the given roots for a PDF whose hash-based DOI
    matches the target DOI. You can replace this with your own matching logic.
    """
    for root in roots:
        root = Path(root)
        if not root.exists():
            continue

        for pdf in root.rglob("*.pdf"):
            try:
                pdf_hash_doi = make_pdf_hash_doi(str(pdf))
                if pdf_hash_doi == doi:
                    return str(pdf)
            except Exception:
                pass

    return None


# ------------------------------------------------------------
# Main function: build bundle from DOI
# ------------------------------------------------------------
def build_bundle_from_doi(doi: str, pdf_roots: list[str]) -> OpenAlexIngestionBundle:
    errors = []
    doi = canonicalise_doi(doi)

    query_metadata = {
        "pdf": {},
        "crossref": {},
        "openalex": {},
        "search_hits_crossref": [],
        "search_hits_openalex": [],
    }

    work_id = f"doi:{doi}"

    # --- CrossRef ---
    cr_meta, cr_err = lookup_crossref_metadata(doi)
    query_metadata["crossref"] = cr_meta
    errors.extend(cr_err)

    # --- OpenAlex ---
    oa_meta, oa_err = lookup_openalex_metadata(doi)
    query_metadata["openalex"] = oa_meta
    errors.extend(oa_err)

    return OpenAlexIngestionBundle(
        work_id=work_id,
        query_metadata=query_metadata,
        retrieval_timestamp=datetime.now(timezone.utc),
        errors=errors,
    )

# ------------------------------------------------------------
# Main function: run two searches → union DOIs → build bundles
# ------------------------------------------------------------
def build_bundles_from_query(
        query: str, 
        pdf_roots: 
        list[str], 
        limit: int = 10, 
        topics: list[str] | None = None) -> list[OpenAlexIngestionBundle]:

    # 1. Run both searches
    crossref_hits = crossref_search_query(query, limit=limit)
    openalex_hits = openalex_search_query(query, limit=limit, topics=topics)
    # 2. Extract DOIs
    dois = set()

    for item in crossref_hits:
        doi = canonicalise_doi(item.get("doi"))
        if doi:
            dois.add(doi)

    for item in openalex_hits:
        doi = canonicalise_doi(item.get("doi"))
        if doi:
            dois.add(doi)

    # 3. Build bundles for each DOI
    bundles = {}
    for doi in tqdm(dois, desc=f"Building bundles for query: {query}", unit="bundle"):
        bundles[doi] = build_bundle_from_doi(doi, pdf_roots)
        bundles[doi].query_metadata["source_query"] = query

    # 4. Attach search hits to bundles
    for item in crossref_hits:
        doi = canonicalise_doi(item.get("doi"))
        if doi in bundles:
            bundles[doi].query_metadata["search_hits_crossref"].append(item)

    for item in openalex_hits:
        doi = canonicalise_doi(item.get("doi"))
        if doi in bundles:
            bundles[doi].query_metadata["search_hits_openalex"].append(item)

    return list(bundles.values())
