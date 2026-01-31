# PaperSearch Agent Instructions

## Architecture Overview

PaperSearch is a research paper metadata ingestion and search system with a three-stage pipeline:

1. **Ingestion** (`src/PaperSearch/ingestion/`) → Raw metadata bundles
2. **Normalization** (`src/PaperSearch/normalization/`, `src/PaperSearch/sql/normalized_store/`) → Canonical records
3. **Indexing** (`src/PaperSearch/indexing/`) → Hybrid BM25 + embedding search

### Data Flow

```
PDF/DOI/Query → bundle_generator.py → raw_bundles table (SQLite)
                     ↓
              normalize.py → normalized_works table
                     ↓
              build_embeddings.py + bm25_index.py → search indices
                     ↓
              hybrid_search.py → ranked results
```

## Critical Patterns

### Identity Resolution
Papers are identified using a priority hierarchy implemented in `bundle_generator.py`:
1. Canonical DOI (from Crossref/OpenAlex)
2. arXiv ID (format: `arxiv:XXXX.XXXXX`)
3. Internal DOI from metadata hash (format: `10.0000/{sha1}`)
4. PDF file hash DOI (format: `10.0000/pdf-{sha256}`)

Always use `canonicalise_doi()` from `ingestion/utils.py` when handling DOIs.

### External Service Dependencies

**GROBID** (required): PDF metadata extraction service
- Runs on `http://localhost:8070` (see `grobid_client.py`)
- Must be running before PDF ingestion
- Extracts title, authors, year, DOI, arXiv ID from PDFs

**External APIs** (optional, rate-limited):
- Crossref: `https://api.crossref.org/works` (no key required, 1 req/sec polite)
- OpenAlex: queries via `openalex_client.py` (topics, year_range filters)

### Database Schema

SQLite database with two core tables (see `sql/db/init_db.py`):

**raw_bundles**: Stores ingestion results as JSON blobs
- `work_id`: Identity key (DOI/arXiv/hash-based)
- `pdf_metadata`, `crossref_metadata`, `openalex_metadata`: Source-specific JSON
- `errors`: List of ingestion warnings/failures

**normalized_works**: Canonical paper records after deduplication
- `work_id`: OpenAlex ID if available
- `doi`: Canonical DOI
- `title`, `authors`, `year`: Merged from best source
- `provenance`: JSON tracking which source provided each field

Use `get_db()` context manager from `sql/db/connection.py` for all DB access.

### Synonym Expansion for Search

BM25 index uses domain-specific synonym expansion (see `indexing/normalizer.py`):
- `SYNONYMS` dict in `indexing/synonym_map.py` maps canonical terms to variants
- Example: "gridworld" matches "grid world", "grid-world", "grid navigation"
- Apply `normalize_text()` to both documents and queries

### Ingestion Bundle Pattern

All ingestion entry points return `OpenAlexIngestionBundle` objects:
- `build_bundle_from_pdf(pdf_path)` - Local PDF file
- `build_bundle_from_doi(doi)` - Known DOI
- `build_bundles_from_query(query, limit, topics, year_range)` - Search-based discovery

Store bundles using `sql/ingestion_store/store_bundle.py`.

## Development Workflows

### Adding New Papers
```python
from PaperSearch.src.PaperSearch.ingestion.bundle_generator import build_bundle_from_pdf
from PaperSearch.src.PaperSearch.sql.ingestion_store.store_bundle import store_bundle

bundle = build_bundle_from_pdf("/path/to/paper.pdf")
store_bundle("data/db/papers.db", bundle)
```

### Running Search
```python
from PaperSearch.src.PaperSearch.indexing.hybrid_search import HybridSearch

# Load pre-built indices
search = HybridSearch(bm25_index, embedding_index, "data/db/papers.db")
results = search.search("reinforcement learning", top_k=20, alpha=1.0)
```

### Module Import Paths
Always use absolute imports from package root: `from PaperSearch.src.PaperSearch.module import func`

## Key Files Reference

- `ingestion/bundle_generator.py` - Core ingestion orchestration
- `sql/db/init_db.py` - Database schema definition
- `sql/normalized_store/normalize.py` - Identity resolution and deduplication
- `indexing/hybrid_search.py` - Final search API combining BM25 + embeddings
- `utils/grobid_tei_parser.py` - TEI XML parsing from GROBID output
- `utils/doi_extractor.py` - Multi-strategy DOI extraction from PDFs

## Common Issues

- **GROBID not running**: Check `http://localhost:8070/api/isalive` before PDF ingestion
- **Import errors**: Ensure working directory is package root and paths use `PaperSearch.src.PaperSearch.*`
- **Duplicate work_id conflicts**: Check `UNIQUE(work_id, retrieval_timestamp)` constraint in schema
- **Empty search results**: Verify indices are built and finalized (`bm25.finalize()` must be called)
