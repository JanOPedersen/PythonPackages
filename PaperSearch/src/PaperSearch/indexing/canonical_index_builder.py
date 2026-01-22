# src/PaperSearch/indexing/canonical_index_builder.py

import sqlite3
import json
from typing import Dict, Any, Iterable, Tuple

from .bm25_index import BM25Index


def inverted_index_to_text(inv_idx: Dict[str, list]) -> str:
    if not inv_idx:
        return ""
    max_pos = max(max(pos_list) for pos_list in inv_idx.values())
    tokens = [""] * (max_pos + 1)
    for token, positions in inv_idx.items():
        for p in positions:
            tokens[p] = token
    return " ".join(t for t in tokens if t)


def safe_load_metadata(raw_md: str | None) -> Dict[str, Any]:
    if not raw_md or raw_md == "null":
        return {}
    try:
        md = json.loads(raw_md)
        if md is None:
            return {}
        if isinstance(md, dict):
            return md
        return {}
    except Exception:
        return {}


def extract_concepts(md: Dict[str, Any]) -> list[tuple[str, float]]:
    concepts = md.get("concepts") or []
    out: list[tuple[str, float]] = []
    for c in concepts:
        cid = c.get("id")
        score = c.get("score", 0.0)
        if cid:
            out.append((cid, float(score)))
    return out


def iter_canonical_docs(conn: sqlite3.Connection) -> Iterable[Tuple[str, str, list[tuple[str, float]]]]:
    rows = conn.execute("SELECT work_id, title, openalex_metadata FROM normalized_works")
    for row in rows:
        raw_md = row["openalex_metadata"] if "openalex_metadata" in row.keys() else None
        md = safe_load_metadata(raw_md)

        abstract = inverted_index_to_text(md.get("abstract_inverted_index") or {})
        text = " ".join(filter(None, [row["title"], abstract]))
        concepts = extract_concepts(md)

        yield row["work_id"], text, concepts


def build_canonical_bm25_index(db_path: str) -> BM25Index:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row

    index = BM25Index()
    doc_id = 0

    for work_id, text, concepts in iter_canonical_docs(conn):
        if text.strip():
            index.add_document(doc_id, work_id, text, concepts=concepts)
            doc_id += 1

    index.finalize()
    conn.close()
    return index
