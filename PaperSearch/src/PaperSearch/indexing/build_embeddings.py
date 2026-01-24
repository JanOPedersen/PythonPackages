# build_embeddings.py

from .embedding_index import EmbeddingIndex
from .canonical_index_builder import iter_canonical_docs
from PaperSearch.src.PaperSearch.sql.db.connection import get_db

def build_embedding_index(db_path: str):
    emb = EmbeddingIndex(db_path)

    # 1. Read all docs first (no writes yet)
    docs = []
    with get_db(db_path) as conn:
        for work_id, text, _concepts in iter_canonical_docs(conn):
            docs.append((work_id, text))

    # 2. Now write embeddings (no read cursor open)
    for work_id, text in docs:
        emb.add(work_id, text)

    return emb
