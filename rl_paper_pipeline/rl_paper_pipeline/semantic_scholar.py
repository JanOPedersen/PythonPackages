import requests
from .config import SEMANTIC_SCHOLAR_API, SEMANTIC_FIELDS

def search_semantic_scholar(query, limit=20):
    params = {
        "query": query,
        "limit": limit,
        "fields": SEMANTIC_FIELDS
    }
    response = requests.get(SEMANTIC_SCHOLAR_API, params=params)
    response.raise_for_status()
    return response.json().get("data", [])
