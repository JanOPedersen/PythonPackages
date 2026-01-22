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
CREATE TABLE normalized_works (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    work_id TEXT,            -- canonical OpenAlex ID (nullable)
    doi TEXT,                -- canonical DOI (nullable)
    title TEXT,
    authors TEXT,            -- JSON list
    year INTEGER,

    alternate_dois TEXT,     -- JSON list of all DOIs seen
    source_bundle_ids TEXT,  -- JSON list of raw bundle IDs merged into this record

    provenance TEXT,         -- JSON dict: { "doi": "crossref", "title": "openalex", ... }
    confidence REAL,         -- 0.0–1.0 score

    created_at TEXT,
    updated_at TEXT
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
 