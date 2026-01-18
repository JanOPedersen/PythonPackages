# ingestion/arxiv_ingestor.py
import arxiv
import uuid
from typing import List
from ingestion.models import Paper


def fetch_arxiv_results(query: str, max_results: int = 50) -> List[arxiv.Result]:
    """
    Query arXiv using the official client.
    Example query: 'cat:cs.LG OR cat:cs.IR'
    """
    search = arxiv.Search(
        query=query,
        max_results=max_results,
        sort_by=arxiv.SortCriterion.SubmittedDate,
    )
    return list(search.results())


def arxiv_result_to_paper(result: arxiv.Result) -> Paper:
    arxiv_id = result.get_short_id()

    # Construct arXiv DOI
    arxiv_doi = f"10.48550/arXiv.{arxiv_id}"

    return Paper(
        paper_id=arxiv_id,
        doi=arxiv_doi,  # always present
        title=result.title.strip(),
        abstract=result.summary.strip(),
        authors=[a.name for a in result.authors],
        year=result.published.year if result.published else None,
        venue="arXiv",
        pdf_path=None,
        full_text=None,
        references=[],
        source="arxiv",
        user_tags=list(result.categories),
        projects=[],
        extra={
            "arxiv_id": arxiv_id,
            "arxiv_primary_category": result.primary_category,
            "arxiv_url": result.entry_id,
        },
    )



def ingest_arxiv_query(query: str, max_results: int = 50) -> List[Paper]:
    """
    High-level ingestion: run a query, convert results to Paper objects.
    """
    results = fetch_arxiv_results(query, max_results=max_results)
    return [arxiv_result_to_paper(r) for r in results]
