# ingestion/enrichers.py
from ingestion.models import Paper


def enrich_with_crossref(paper: Paper) -> Paper:
    """
    Given a DOI, call Crossref and fill in missing fields:
    - abstract
    - references (DOIs)
    - better venue/year if needed
    """
    # Stub: implement real HTTP calls + parsing
    return paper


def enrich_with_semantic_scholar(paper: Paper) -> Paper:
    """
    Given a DOI or title, call Semantic Scholar:
    - citations
    - influential citations
    - fields of study
    """
    # Stub: implement real HTTP calls + parsing
    return paper
