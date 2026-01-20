from typing import Dict
from core.query import QueryRepresentation
from core.document import Document
from indexing.text_index import TextIndex

class Recommender:
    def __init__(self, text_index: TextIndex, documents: Dict[str, Document]):
        self.text_index = text_index
        self.documents = documents

    def recommend(self, query: QueryRepresentation, k: int = 10):
        hits = self.text_index.search(query.raw_text, k=50)
        scored = [(self.documents[doc_id], score) for doc_id, score in hits]
        scored.sort(key=lambda x: x[1], reverse=True)
        return scored[:k]
 