import requests
from .config import OPENALEX_BASE, RL_CONCEPT_ID, MAX_RESULTS

def search_openalex_rl():
    params = {
        "filter": f"concepts.id:{RL_CONCEPT_ID}",
        "sort": "publication_date:desc",
        "per-page": MAX_RESULTS
    }

    response = requests.get(OPENALEX_BASE, params=params)
    response.raise_for_status()

    return response.json().get("results", [])
