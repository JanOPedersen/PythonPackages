import requests
from .utils import canonicalise_doi

CROSSREF_BASE_URL = "https://api.crossref.org/works"

# -----------------------------
# CrossRef search
# -----------------------------
def search_crossref_query(
        query: str, 
        limit: int = 10,
        fields: list[str] | None = None,
    ):
    url = CROSSREF_BASE_URL
    params = {"query": query, "rows": limit}

    r = requests.get(url, params=params, timeout=10)
    r.raise_for_status()

    items = r.json()["message"]["items"]

    # If no field filtering requested, return full items
    if not fields:
        return items

    # Otherwise return only the selected subset
    filtered = []
    for item in items:
        filtered.append({f: item.get(f) for f in fields})

    return filtered


def crossref_search_query(query: str, limit: int = 10):
    results = search_crossref_query(query,
    fields=["title", "DOI", "author","published","is-referenced-by-count","reference"],
    limit=limit)
    for work in results:
        doi = work.get("DOI")
        if doi:
            work["DOI"] = canonicalise_doi(doi)
    return results

def crossref_search_doi(doi: str) -> dict | None:
    url = f"{CROSSREF_BASE_URL}/works/{doi}"
    resp = requests.get(url, timeout=10)

    if resp.status_code != 200:
        return None

    data = resp.json().get("message", {})

    return {
        "title": data.get("title", [None])[0],
        "author": [
            {
                "name": f"{a.get('given', '')} {a.get('family', '')}".strip(),
                "orcid": a.get("ORCID"),
                "affiliation": a.get("affiliation", [])
            }
            for a in data.get("author", [])
        ],
        "year": data.get("issued", {}).get("date-parts", [[None]])[0][0],
        "references_count": data.get("references-count"),
        "is_referenced_by_count": data.get("is-referenced-by-count"),
        "DOI": canonicalise_doi(data.get("DOI")),
        "URL": data.get("URL"),
        "reference": data.get("reference", []),
    }