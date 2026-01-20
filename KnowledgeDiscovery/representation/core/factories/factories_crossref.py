import requests

def from_doi(doi: str) -> dict | None:
    url = f"https://api.crossref.org/works/{doi}"
    resp = requests.get(url, timeout=10)

    if resp.status_code != 200:
        return None

    data = resp.json().get("message", {})

    return {
        "title": data.get("title", [None])[0],
        "authors": [
            {
                "name": f"{a.get('given', '')} {a.get('family', '')}".strip(),
                "orcid": a.get("ORCID"),
                "affiliation": a.get("affiliation", [])
            }
            for a in data.get("author", [])
        ],
        "venue": data.get("container-title", [None])[0],
        "year": data.get("issued", {}).get("date-parts", [[None]])[0][0],
        "publisher": data.get("publisher"),
        "references_count": data.get("references-count"),
        "is_referenced_by_count": data.get("is-referenced-by-count"),
    }
