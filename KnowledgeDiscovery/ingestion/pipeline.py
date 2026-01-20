# ingestion/pipeline.py
from pathlib import Path
from typing import List
from ingestion.zotero_ingestor import ingest_zotero_json
from ingestion.pdf_utils import attach_pdf_and_text
from ingestion.enrichers import enrich_with_crossref, enrich_with_semantic_scholar
from ingestion.dedup import deduplicate_papers
from ingestion.db import get_engine, init_db, upsert_papers
from ingestion.models import Paper


def run_ingestion(
    zotero_json_path: str,
    pdf_root: str,
    db_path: str = "papers.db",
    do_enrich: bool = False,
) -> None:
    # 1. Load from Zotero
    papers: List[Paper] = ingest_zotero_json(zotero_json_path)

    # 2. Attach PDFs + full text
    pdf_root_path = Path(pdf_root)
    papers = [attach_pdf_and_text(p, pdf_root_path) for p in papers]

    # 3. Optional enrichment
    if do_enrich:
        enriched: List[Paper] = []
        for p in papers:
            if p.doi:
                p = enrich_with_crossref(p)
                p = enrich_with_semantic_scholar(p)
            enriched.append(p)
        papers = enriched

    # 4. Deduplicate
    papers = deduplicate_papers(papers)

    # 5. Store in DB
    engine = get_engine(db_path)
    init_db(engine)
    upsert_papers(engine, papers)


if __name__ == "__main__":
    run_ingestion(
        zotero_json_path="zotero_export.json",
        pdf_root="/path/to/pdfs",
        db_path="papers.db",
        do_enrich=False,
    )
