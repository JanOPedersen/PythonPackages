# ingestion/dedup.py
from typing import List, Dict
from ingestion.models import Paper


def deduplicate_papers(papers: List[Paper]) -> List[Paper]:
    """
    Simple strategy:
    - Prefer DOI as key when present
    - Fallback to title normalized
    - Merge metadata when duplicates found
    """
    by_key: Dict[str, Paper] = {}

    def make_key(p: Paper) -> str:
        if p.doi:
            return f"doi:{p.doi.lower()}"
        return f"title:{p.title.strip().lower()}"

    for p in papers:
        key = make_key(p)
        if key not in by_key:
            by_key[key] = p
        else:
            existing = by_key[key]
            # Merge logic: prefer existing, fill gaps
            if not existing.abstract and p.abstract:
                existing.abstract = p.abstract
            if not existing.venue and p.venue:
                existing.venue = p.venue
            if not existing.year and p.year:
                existing.year = p.year
            # Merge tags, projects, references
            existing.user_tags = sorted(set(existing.user_tags + p.user_tags))
            existing.projects = sorted(set(existing.projects + p.projects))
            existing.references = sorted(set(existing.references + p.references))
            # Keep best pdf/full_text if missing
            if not existing.pdf_path and p.pdf_path:
                existing.pdf_path = p.pdf_path
                existing.full_text = p.full_text
            # You can also merge extra fields if needed
            by_key[key] = existing

    return list(by_key.values())
