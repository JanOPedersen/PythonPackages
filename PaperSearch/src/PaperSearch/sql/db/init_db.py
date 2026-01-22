import sqlite3
from pathlib import Path

SCHEMA = """
-- ============================================================
-- RAW INGESTION BUNDLES
-- ============================================================
CREATE TABLE IF NOT EXISTS raw_bundles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    work_id TEXT NOT NULL,
    doi TEXT,
    arxiv_id TEXT,

    retrieval_timestamp TEXT NOT NULL,

    pdf_metadata TEXT,
    crossref_metadata TEXT,
    openalex_metadata TEXT,
    search_hits_crossref TEXT,
    search_hits_openalex TEXT,

    errors TEXT,

    source_query TEXT,
    source_pdf_path TEXT,

    UNIQUE(work_id, retrieval_timestamp)
);

CREATE INDEX IF NOT EXISTS idx_raw_bundles_doi
    ON raw_bundles(doi);

CREATE INDEX IF NOT EXISTS idx_raw_bundles_work_id
    ON raw_bundles(work_id);


-- ============================================================
-- NORMALIZED WORKS
-- ============================================================
CREATE TABLE IF NOT EXISTS normalized_works (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    work_id TEXT NOT NULL UNIQUE,
    doi TEXT,
    arxiv_id TEXT,

    title TEXT,
    authors TEXT,
    year INTEGER,

    source_pdf BOOLEAN,
    source_crossref BOOLEAN,
    source_openalex BOOLEAN,

    merged_metadata TEXT,

    normalized_timestamp TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_normalized_doi
    ON normalized_works(doi);

CREATE INDEX IF NOT EXISTS idx_normalized_work_id
    ON normalized_works(work_id);


-- ============================================================
-- API CACHE
-- ============================================================
CREATE TABLE IF NOT EXISTS api_cache (
    key TEXT PRIMARY KEY,
    response TEXT NOT NULL,
    timestamp TEXT NOT NULL
);


-- ============================================================
-- PDF FILE REGISTRY
-- ============================================================
CREATE TABLE IF NOT EXISTS pdf_files (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    path TEXT NOT NULL UNIQUE,
    hash_doi TEXT,
    extracted_metadata TEXT,
    last_scanned TEXT
);

CREATE INDEX IF NOT EXISTS idx_pdf_hash_doi
    ON pdf_files(hash_doi);
"""


def init_ingestion_db(db_path: str):
    """
    Initialize the SQLite database with all required tables and indexes.
    Safe to run multiple times.
    """
    db_path = Path(db_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(db_path)
    try:
        conn.executescript(SCHEMA)
        conn.commit()
    finally:
        conn.close()
 