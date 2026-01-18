# ingestion/csl_json_ingestor.py
import json
import uuid
from typing import List, Dict, Any
from ingestion.models import Paper


def load_csl_json(path: str) -> List[Dict[str, Any]]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def csl_item_to_paper(item: Dict[str, Any]) -> Paper:
    """
    Convert a CSL-JSON item into your canonical Paper model.
    CSL JSON example fields:
      - id
      - type
      - title
      - author: [{family, given}]
      - issued: {"date-parts": [[2020]]}
      - URL
      - DOI
      - note
    """

    # 1. Paper ID
    paper_id = item.get("id") or str(uuid.uuid4())

    # 2. Title
    title = item.get("title", "Untitled").strip()

    # 3. Authors
    authors = []
    for a in item.get("author", []):
        family = a.get("family")
        given = a.get("given")
        if family and given:
            authors.append(f"{given} {family}")
        elif family:
            authors.append(family)
        elif given:
            authors.append(given)

    # 4. Year
    year = None
    issued = item.get("issued", {})
    if "date-parts" in issued:
        parts = issued["date-parts"]
        if parts and parts[0] and isinstance(parts[0][0], int):
            year = parts[0][0]

    # 5. DOI
    doi = item.get("DOI")

    # 6. URL
    url = item.get("URL")

    # 7. Notes (often contain metadata)
    note = item.get("note", "")

    # 8. Tags (CSL JSON doesn't have Zotero tags, but you can parse from note)
    user_tags = []
    if "UDC:" in note:
        # Example: "UDC: 0"
        try:
            udc = note.split("UDC:")[1].strip().split()[0]
            user_tags.append(f"UDC:{udc}")
        except Exception:
            pass

    # 9. Build canonical Paper
    return Paper(
        paper_id=paper_id,
        doi=doi,
        title=title,
        abstract=None,  # CSL JSON rarely includes abstracts
        authors=authors,
        year=year,
        venue=item.get("container-title"),
        pdf_path=None,
        full_text=None,
        references=[],  # CSL JSON does not include references
        source="csl-json",
        user_tags=user_tags,
        projects=[],
        extra={
            "url": url,
            "note": note,
            "type": item.get("type"),
        },
    )


def ingest_csl_json(path: str) -> List[Paper]:
    items = load_csl_json(path)
    papers = []
    for item in items:
        # Only ingest items that look like papers
        if item.get("type") in {"article-journal", "report", "paper-conference", "chapter"}:
            papers.append(csl_item_to_paper(item))
    return papers
