import requests

OPENALEX_API_BASE_URL = "https://api.openalex.org/works"

def search_openalex_query(
    query: str,
    limit: int = 10,
    fields: list[str] | None = None,
    expand: list[str] | None = None,
):
    url = OPENALEX_API_BASE_URL
    
    params = {
        "search": query,
        "per-page": limit,
    }

    # Add metadata field selection
    if fields:
        params["select"] = ",".join(fields)

    # Add expansion of nested metadata
    if expand:
        params["expand"] = ",".join(expand)

    r = requests.get(url, params=params, timeout=10)
    r.raise_for_status()
    return r.json().get("results", [])

def openalex_search_query(query: str, limit: int = 10):
    results = search_openalex_query(query,
    fields=["id", "doi", "title", "publication_year", "authorships", "concepts", "cited_by_count","referenced_works"],
    limit=limit)
    return results

def openalex_search_doi(doi: str) -> dict | None:
    url = f"{OPENALEX_API_BASE_URL}/works/https://doi.org/{doi}"
    resp = requests.get(url, timeout=10)

    if resp.status_code != 200:
        return None

    data = resp.json()

    return {
        "concepts": [c["display_name"] for c in data.get("concepts", [])],
        "cited_by_count": data.get("cited_by_count"),
        "referenced_works": data.get("referenced_works", []),
        "id": data.get("id"),
        "title": data.get("title"),
        "publication_year": data.get("publication_year"),
        "authorships": data.get("authorships", []),
        "doi": data.get("doi"),
    }