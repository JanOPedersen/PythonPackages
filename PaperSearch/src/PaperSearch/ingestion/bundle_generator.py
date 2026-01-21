from dataclasses import dataclass
from datetime import datetime, timezone

# --- your imports ---
from PaperSearch.src.PaperSearch.ingestion.grobid_client import grobid_search_pdf
from PaperSearch.src.PaperSearch.ingestion.utils import (
    canonicalise_doi,
    make_internal_doi,
    make_pdf_hash_doi,
)
from PaperSearch.src.PaperSearch.ingestion.crossref_client import crossref_search_doi
from PaperSearch.src.PaperSearch.ingestion.openalex_client import openalex_search_doi

@dataclass
class OpenAlexIngestionBundle:
    work_id: str
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
    if pdf_doi:
        work_id = f"doi:{pdf_doi}"
    elif pdf_arxiv:
        work_id = f"arxiv:{pdf_arxiv}"
    elif pdf_title and pdf_authors and pdf_year:
        work_id = make_internal_doi(pdf_title, pdf_authors, pdf_year)
    else:
        work_id = make_pdf_hash_doi(pdf_path)

    crossref_data = None
    openalex_data = None
    if pdf_doi:
    # ------------------------------------------------------------
    # 3. Crossref lookup (using crossref_search_query)
    # ------------------------------------------------------------
        try:
            crossref_data = crossref_search_doi(pdf_doi)
            if crossref_data:
                if "DOI" in crossref_data:
                    query_metadata["crossref"]["doi"] = crossref_data["DOI"]
                if "author" in crossref_data:
                    query_metadata["crossref"]["authors"] = crossref_data["author"]
                if "year" in crossref_data:
                    query_metadata["crossref"]["year"] = crossref_data["year"]
                if "title" in crossref_data:
                    query_metadata["crossref"]["title"] = crossref_data["title"]
        except Exception as e:
            errors.append(f"Crossref lookup failed: {e}")
            query_metadata["crossref"]["error"] = str(e)

    # ------------------------------------------------------------
    # 4. OpenAlex lookup (using openalex_search_query)
    # ------------------------------------------------------------
        try:
            openalex_data = openalex_search_doi(pdf_doi)
            if openalex_data:
                if "doi" in openalex_data:
                    query_metadata["openalex"]["doi"] = openalex_data["doi"]
                if "authorships" in openalex_data:
                    query_metadata["openalex"]["authors"] = openalex_data["authorships"]
                if "publication_year" in openalex_data:
                    query_metadata["openalex"]["year"] = openalex_data["publication_year"]
                if "title" in openalex_data:
                    query_metadata["openalex"]["title"] = openalex_data["title"]
        except Exception as e:
            errors.append(f"OpenAlex DOI lookup failed: {e}")
            query_metadata["openalex"]["error"] = str(e)

    # ------------------------------------------------------------
    # 5. Assemble bundle
    # ------------------------------------------------------------
    bundle = OpenAlexIngestionBundle(
        work_id=work_id,
        query_metadata=query_metadata,
        retrieval_timestamp = datetime.now(timezone.utc),
        errors=None,
    )

    return bundle

