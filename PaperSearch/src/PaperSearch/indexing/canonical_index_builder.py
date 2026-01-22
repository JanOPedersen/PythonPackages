import sqlite3
import json
from .bm25_index import BM25Index


def inverted_index_to_text(inv_idx: dict) -> str:
    if not inv_idx:
        return ""
    max_pos = max(max(pos_list) for pos_list in inv_idx.values())
    tokens = [""] * (max_pos + 1)
    for token, positions in inv_idx.items():
        for p in positions:
            tokens[p] = token
    return " ".join(t for t in tokens if t)


def iter_canonical_docs(conn):
    rows = conn.execute("SELECT work_id, title, openalex_metadata FROM normalized_works")
    for row in rows:
        raw_md = row["openalex_metadata"]

        # Robust JSON loading
        if not raw_md or raw_md == "null":
            md = {}
        else:
            try:
                md = json.loads(raw_md)
                if md is None:
                    md = {}
            except Exception:
                md = {}

        abstract = inverted_index_to_text(md.get("abstract_inverted_index") or {})
        text = " ".join(filter(None, [row["title"], abstract]))
        yield row["work_id"], text



def build_canonical_bm25_index(db_path: str) -> BM25Index:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row

    index = BM25Index()
    doc_id = 0

    for work_id, text in iter_canonical_docs(conn):
        if text.strip():
            index.add_document(doc_id, work_id, text)
            doc_id += 1

    index.finalize()
    conn.close()
    return index
 