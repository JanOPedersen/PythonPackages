import requests

def from_doi(doi: str) -> dict | None:
    url = f"https://api.openalex.org/works/https://doi.org/{doi}"
    resp = requests.get(url, timeout=10)

    if resp.status_code != 200:
        return None

    data = resp.json()

    return {
        "concepts": [c["display_name"] for c in data.get("concepts", [])],
        "citations": data.get("cited_by_count"),
        "references": data.get("referenced_works", []),
        "related_works": data.get("related_works", []),
        "openalex_id": data.get("id"),
        "primary_location": data.get("primary_location", {}),
    }
