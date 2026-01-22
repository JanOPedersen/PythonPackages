import sqlite3
import json
from datetime import datetime
from typing import Iterable, List
from tqdm import tqdm


# ------------------------------------------------------------
# RawBundle model
# ------------------------------------------------------------
class RawBundle:
    def __init__(self, row):
        self.id = row["id"]
        self.work_id = row["work_id"]
        self.doi = row["doi"]
        self.arxiv_id = row["arxiv_id"]
        self.retrieval_timestamp = row["retrieval_timestamp"]

        self.pdf_metadata = json.loads(row["pdf_metadata"])
        self.crossref_metadata = json.loads(row["crossref_metadata"])
        self.openalex_metadata = json.loads(row["openalex_metadata"])

        self.search_hits_crossref = json.loads(row["search_hits_crossref"])
        self.search_hits_openalex = json.loads(row["search_hits_openalex"])

        self.errors = json.loads(row["errors"])
        self.source_query = row["source_query"]
        self.source_pdf_path = row["source_pdf_path"]

    @property
    def query_metadata(self):
        return {
            "pdf": self.pdf_metadata,
            "crossref": self.crossref_metadata,
            "openalex": self.openalex_metadata,
            "search_hits_crossref": self.search_hits_crossref,
            "search_hits_openalex": self.search_hits_openalex,
            "source_query": self.source_query,
        }


# ------------------------------------------------------------
# DOI selection
# ------------------------------------------------------------
def pick_canonical_doi(md):
    pdf_doi = md["pdf"].get("doi")
    cr_doi = md["crossref"].get("doi")
    oa_doi = md["openalex"].get("doi")

    if cr_doi:
        return cr_doi, "crossref"
    if oa_doi:
        return oa_doi, "openalex"
    if pdf_doi:
        return pdf_doi, "pdf"
    return None, None


# ------------------------------------------------------------
# Normalizer
# ------------------------------------------------------------
class Normalizer:
    def __init__(self, db_path: str):
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row

    # -----------------------------
    # Streaming group loaders
    # -----------------------------
    def load_group_by_work_id(self, work_id) -> Iterable[RawBundle]:
        rows = self.conn.execute(
            "SELECT * FROM raw_bundles WHERE work_id = ?", (work_id,)
        )
        for row in rows:
            yield RawBundle(row)

    def load_group_by_doi(self, doi) -> Iterable[RawBundle]:
        rows = self.conn.execute(
            "SELECT * FROM raw_bundles WHERE work_id IS NULL AND doi = ?", (doi,)
        )
        for row in rows:
            yield RawBundle(row)

    def load_unresolved(self, bundle_id) -> Iterable[RawBundle]:
        row = self.conn.execute(
            "SELECT * FROM raw_bundles WHERE id = ?", (bundle_id,)
        ).fetchone()
        if row:
            yield RawBundle(row)

    # -----------------------------
    # Identity resolution
    # -----------------------------
    def identity_key(self, bundle: RawBundle):
        md = bundle.query_metadata

        work_id = md["openalex"].get("id")
        doi, _ = pick_canonical_doi(md)

        if work_id:
            return ("work_id", work_id)
        if doi:
            return ("doi", doi)
        return ("unresolved", bundle.id)

    # -----------------------------
    # Merge logic
    # -----------------------------
    def merge_bundles(self, bundles: List[RawBundle]):
        merged = {
            "work_id": None,
            "doi": None,
            "title": None,
            "authors": [],
            "year": None,
            "alternate_dois": set(),
            "source_bundle_ids": [],
            "provenance": {},
        }

        # Metadata
        merged["pdf_metadata"] = None
        merged["crossref_metadata"] = None
        merged["openalex_metadata"] = None

        for b in bundles:
            md = b.query_metadata
            merged["source_bundle_ids"].append(b.id)

            # DOI
            doi, source = pick_canonical_doi(md)
            if doi:
                merged["alternate_dois"].add(doi)
                if merged["doi"] is None:
                    merged["doi"] = doi
                    merged["provenance"]["doi"] = source

            # work_id: prefer OpenAlex ID, else existing bundle.work_id, else DOI-based synthetic ID
            if merged["work_id"] is None:
                oa_id = md["openalex"].get("id")
                if oa_id:
                    merged["work_id"] = oa_id
                elif b.work_id:
                    merged["work_id"] = b.work_id
                elif merged["doi"]:
                    merged["work_id"] = f"doi:{merged['doi']}"


            # title
            title = (
                md["openalex"].get("title")
                or md["crossref"].get("title")
                or md["pdf"].get("title")
            )
            if merged["title"] is None and title:
                merged["title"] = title
                merged["provenance"]["title"] = (
                    "openalex" if md["openalex"].get("title") else
                    "crossref" if md["crossref"].get("title") else
                    "pdf"
                )

            # authors
            authors = (
                md["openalex"].get("authors")
                or md["crossref"].get("authors")
                or md["pdf"].get("authors")
            )
            if merged["authors"] == [] and authors:
                merged["authors"] = authors
                merged["provenance"]["authors"] = (
                    "openalex" if md["openalex"].get("authors") else
                    "crossref" if md["crossref"].get("authors") else
                    "pdf"
                )

            # year
            year = (
                md["crossref"].get("year")
                or md["openalex"].get("year")
                or md["pdf"].get("year")
            )
            if merged["year"] is None and year:
                merged["year"] = year
                merged["provenance"]["year"] = (
                    "crossref" if md["crossref"].get("year") else
                    "openalex" if md["openalex"].get("year") else
                    "pdf"
                )

            # PDF metadata
            if merged["pdf_metadata"] is None and b.pdf_metadata:
                merged["pdf_metadata"] = b.pdf_metadata

            # Crossref metadata
            if merged["crossref_metadata"] is None and b.crossref_metadata:
                merged["crossref_metadata"] = b.crossref_metadata

            # OpenAlex metadata
            if merged["openalex_metadata"] is None and b.openalex_metadata:
                merged["openalex_metadata"] = b.openalex_metadata

        merged["alternate_dois"] = list(merged["alternate_dois"])
        merged["confidence"] = self.compute_confidence(merged)

        return merged

    # -----------------------------
    # Confidence scoring
    # -----------------------------
    def compute_confidence(self, m):
        score = 0.0
        if m["doi"]:
            score += 0.4
        if m["work_id"]:
            score += 0.3
        if m["title"]:
            score += 0.2
        if m["authors"]:
            score += 0.1
        return score

    # -----------------------------
    # Store normalized record
    # -----------------------------
    def store_normalized(self, m):
        now = datetime.utcnow().isoformat()

        self.conn.execute("""
            INSERT INTO normalized_works (
                work_id, doi, title, authors, year,
                alternate_dois, source_bundle_ids,
                provenance, confidence,
                created_at, updated_at,
                pdf_metadata, crossref_metadata, openalex_metadata
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            m["work_id"],
            m["doi"],
            m["title"],
            json.dumps(m["authors"]),
            m["year"],
            json.dumps(m["alternate_dois"]),
            json.dumps(m["source_bundle_ids"]),
            json.dumps(m["provenance"]),
            m["confidence"],
            now,
            now,
            json.dumps(m["pdf_metadata"]),
            json.dumps(m["crossref_metadata"]),
            json.dumps(m["openalex_metadata"]),
        ))
        self.conn.commit()

    # -----------------------------
    # Full streaming normalization
    # -----------------------------
    def normalize_database(self):
        # Count groups for progress bar
        count_work_id = self.conn.execute(
            "SELECT COUNT(DISTINCT work_id) FROM raw_bundles WHERE work_id IS NOT NULL"
        ).fetchone()[0]

        count_doi = self.conn.execute(
            "SELECT COUNT(DISTINCT doi) FROM raw_bundles WHERE work_id IS NULL AND doi IS NOT NULL"
        ).fetchone()[0]

        count_unresolved = self.conn.execute(
            "SELECT COUNT(*) FROM raw_bundles WHERE work_id IS NULL AND doi IS NULL"
        ).fetchone()[0]

        total_groups = count_work_id + count_doi + count_unresolved

        with tqdm(total=total_groups, desc="Normalizing") as pbar:

            # 1. Groups with work_id
            for (work_id,) in self.conn.execute(
                "SELECT DISTINCT work_id FROM raw_bundles WHERE work_id IS NOT NULL"
            ):
                bundles = list(self.load_group_by_work_id(work_id))
                merged = self.merge_bundles(bundles)
                self.store_normalized(merged)
                pbar.update(1)

            # 2. Groups with DOI but no work_id
            for (doi,) in self.conn.execute(
                "SELECT DISTINCT doi FROM raw_bundles WHERE work_id IS NULL AND doi IS NOT NULL"
            ):
                bundles = list(self.load_group_by_doi(doi))
                merged = self.merge_bundles(bundles)
                self.store_normalized(merged)
                pbar.update(1)

            # 3. Unresolved bundles
            for (bundle_id,) in self.conn.execute(
                "SELECT id FROM raw_bundles WHERE work_id IS NULL AND doi IS NULL"
            ):
                bundles = list(self.load_unresolved(bundle_id))
                merged = self.merge_bundles(bundles)
                self.store_normalized(merged)
                pbar.update(1)


# ------------------------------------------------------------
# CLI entry point
# ------------------------------------------------------------

 