import json
from ..db.connection import get_db

def store_bundle(db_path: str, bundle):
    """
    Store a raw ingestion bundle in the SQLite database.
    Matches the schema defined in init_db.py.
    """

    md = bundle.query_metadata

    with get_db(db_path) as conn:
        conn.execute("""
            INSERT INTO raw_bundles (
                work_id,
                doi,
                arxiv_id,
                retrieval_timestamp,
                pdf_metadata,
                crossref_metadata,
                openalex_metadata,
                search_hits_crossref,
                search_hits_openalex,
                errors,
                source_query,
                source_pdf_path
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            bundle.work_id,
            md["pdf"].get("doi"),
            md["pdf"].get("arxiv"),
            bundle.retrieval_timestamp.isoformat(),

            json.dumps(md.get("pdf", {})),
            json.dumps(md.get("crossref", {})),
            json.dumps(md.get("openalex", {})),

            json.dumps(md.get("search_hits_crossref", [])),
            json.dumps(md.get("search_hits_openalex", [])),

            json.dumps(bundle.errors or []),

            md.get("source_query"),      # optional, may be None
            md["pdf"].get("path"),       # store PDF path if available
        ))

def store_bundles(db_path: str, bundles: list):
    """
    Store a list of OpenAlexIngestionBundle objects in the SQLite database.
    Uses a single DB connection for efficiency.
    """

    with get_db(db_path) as conn:
        for bundle in bundles:
            md = bundle.query_metadata

            conn.execute("""
                INSERT INTO raw_bundles (
                    work_id,
                    doi,
                    arxiv_id,
                    retrieval_timestamp,
                    pdf_metadata,
                    crossref_metadata,
                    openalex_metadata,
                    search_hits_crossref,
                    search_hits_openalex,
                    errors,
                    source_query,
                    source_pdf_path
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                bundle.work_id,
                md["pdf"].get("doi"),
                md["pdf"].get("arxiv"),
                bundle.retrieval_timestamp.isoformat(),

                json.dumps(md.get("pdf", {})),
                json.dumps(md.get("crossref", {})),
                json.dumps(md.get("openalex", {})),

                json.dumps(md.get("search_hits_crossref", [])),
                json.dumps(md.get("search_hits_openalex", [])),

                json.dumps(bundle.errors or []),

                md.get("source_query"),
                md["pdf"].get("path"),
            ))

 