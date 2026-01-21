import requests
from KnowledgeDiscovery.recommender.core.embedder import SentenceTransformerEmbedder
from KnowledgeDiscovery.recommender.indexing.vector_index import VectorIndex
from KnowledgeDiscovery.representation.core.factories.document_normalizer import NormalizedDocument
import requests

OPENALEX_BASE = "https://api.openalex.org"

def find_concept_id(name: str, limit: int = 5):
    url = f"{OPENALEX_BASE}/concepts"
    params = {"search": name, "per-page": limit}
    r = requests.get(url, params=params, timeout=10)
    r.raise_for_status()
    results = r.json().get("results", [])
    return [
        {
            "id": c["id"],
            "display_name": c["display_name"],
            "level": c.get("level"),
            "score": c.get("relevance_score"),
        }
        for c in results
    ]


class OnlineDocument:
    def __init__(self, doc_id, title, abstract, authors, year, venue):
        self.doc_id = doc_id
        self.title = title or ""
        self.abstract = abstract or ""
        self.authors = authors or []
        self.year = year
        self.venue = venue

    @classmethod
    def from_openalex(cls, item):
        doc_id = item.get("id")
        title = item.get("title")

        # Convert OpenAlex inverted index to normal text
        inv = item.get("abstract_inverted_index")
        if inv:
            words = sorted(
                ((word, pos[0]) for word, pos in inv.items()),
                key=lambda x: x[1]
            )
            abstract = " ".join(w for w, _ in words)
        else:
            abstract = ""

        authors = [
            a["author"]["display_name"]
            for a in item.get("authorships", [])
        ]

        year = item.get("publication_year")
        venue = item.get("host_venue", {}).get("display_name")

        return cls(doc_id, title, abstract, authors, year, venue)

    def text(self):
        return f"{self.title} {self.abstract}".strip()

    def __repr__(self):
        return f"OnlineDocument({self.doc_id}, title={self.title[:60]!r})"


def search_openalex(query: str, limit: int = 20):
    url = "https://api.openalex.org/works"
    params = {
        "search": query,        # full-text semantic search
        "per-page": limit,
        "sort": "relevance_score:desc"
    }

    r = requests.get(url, params=params, timeout=10)
    r.raise_for_status()
    return r.json().get("results", [])


def online_recommend(query: str, k: int = 10):
    # 1. Search OpenAlex
    results = search_openalex(query, limit=50)

    # 2. Normalize
    docs = [
        OnlineDocument.from_openalex(item)
        for item in results
    ]

    # 3. Build a temporary vector index
    embedder = SentenceTransformerEmbedder()
    index = VectorIndex(dim=384)

    for doc in docs:
        index.add(doc.doc_id, embedder(doc.text()))

    # 4. Embed the query
    qvec = embedder(query)

    # 5. Search
    ranked = index.search(qvec, k=k)

    # 6. Return matching documents
    return [
        next(d for d in docs if d.doc_id == doc_id)
        for doc_id, score in ranked
    ]
 