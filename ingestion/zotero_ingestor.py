# ingestion/zotero_ingestor.py
import json
import uuid
from typing import List
from ingestion.models import Paper


def load_zotero_json(path: str) -> List[dict]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def zotero_item_to_paper(item: dict) -> Paper:
    data = item.get("data", {})
    title = data.get("title") or "Untitled"
    doi = (data.get("DOI") or "").strip() or None
    year = None
    if data.get("date"):
        # crude year extraction
        for token in str(data["date"]).split():
            if token.isdigit() and len(token) == 4:
                year = int(token)
                break

    authors = []
    for c in data.get("creators", []):
        name = " ".join(
            part for part in [c.get("firstName"), c.get("lastName")] if part
        ).strip()
        if name:
            authors.append(name)

    tags = [t.get("tag") for t in data.get("tags", []) if t.get("tag")]

    # You can map collections → projects later if you want
    projects: List[str] = []

    paper_id = data.get("key") or str(uuid.uuid4())

    return Paper(
        paper_id=paper_id,
        doi=doi,
        title=title,
        abstract=None,  # can be enriched later
        authors=authors,
        year=year,
        venue=data.get("publicationTitle"),
        pdf_path=None,  # filled by PDF resolver
        full_text=None,  # filled by PDF extraction
        references=[],  # filled by enrichment
        source="zotero",
        user_tags=tags,
        projects=projects,
        extra={"zotero_raw": data},
    )


def ingest_zotero_json(path: str) -> List[Paper]:
    items = load_zotero_json(path)
    papers: List[Paper] = []
    for item in items:
        if item.get("data", {}).get("itemType") in {"journalArticle", "conferencePaper", "preprint"}:
            papers.append(zotero_item_to_paper(item))
    return papers
