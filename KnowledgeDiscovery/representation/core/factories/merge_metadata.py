import requests

def fetch_openalex_work(work_id: str) -> dict | None:
    """
    Fetch metadata for a single OpenAlex work ID.
    Returns a dict with title, authors, year, doi, venue, etc.
    """
    # Normalize ID
    if work_id.startswith("https://openalex.org/"):
        work_id = work_id.replace("https://openalex.org/", "")

    url = f"https://api.openalex.org/works/{work_id}"

    try:
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        data = r.json()
    except Exception:
        return None

    # Extract authors
    authors = []
    for a in data.get("authorships", []):
        name = a.get("author", {}).get("display_name")
        if name:
            authors.append({"name": name})

    # Extract venue
    venue = None
    if "host_venue" in data and data["host_venue"].get("display_name"):
        venue = data["host_venue"]["display_name"]

    # Extract year
    year = data.get("publication_year")

    # Extract DOI
    doi = None
    if data.get("doi"):
        doi = data["doi"].replace("https://doi.org/", "")

    return {
        "title": data.get("title"),
        "authors": authors,
        "year": year,
        "doi": doi,
        "venue": venue,
        "id": f"https://openalex.org/{work_id}",
    }

def enrich_openalex_references(ref_ids: list[str]) -> list[dict]:
    """
    Given a list of OpenAlex reference IDs, fetch metadata for each
    and return a list of structured reference dicts.
    """
    enriched = []

    for rid in ref_ids:
        meta = fetch_openalex_work(rid)
        if not meta:
            # fallback: store ID only
            enriched.append({"id": rid})
            continue

        enriched.append({
            "title": meta.get("title"),
            "authors": meta.get("authors"),
            "year": meta.get("year"),
            "identifiers": [{"type": "doi", "value": meta["doi"]}] if meta.get("doi") else [],
            "venue": meta.get("venue"),
            "id": meta.get("id"),
        })

    return enriched

def merge_metadata(grobid, crossref, openalex):
    """
    Merge metadata from GROBID, Crossref, and OpenAlex.
    Priority:
        1. GROBID (header > fulltext)
        2. Crossref
        3. OpenAlex
    """

    merged = {}

    # -------------------------
    # Title
    # -------------------------
    merged["title"] = (
        grobid.get("title")
        or (crossref.get("title") if crossref else None)
        or (openalex.get("title") if openalex else None)
    )

    # -------------------------
    # Abstract
    # -------------------------
    merged["abstract"] = (
        grobid.get("abstract")
        or (crossref.get("abstract") if crossref else None)
        or (openalex.get("abstract") if openalex else None)
    )

    # -------------------------
    # Authors
    # -------------------------
    grobid_authors = grobid.get("authors") or []
    crossref_authors = crossref.get("authors") if crossref else None
    openalex_authors = openalex.get("authors") if openalex else None

    # GROBID authors win if they contain real names
    if any(a.get("given") or a.get("family") for a in grobid_authors):
        merged["authors"] = grobid_authors
    else:
        merged["authors"] = (
            crossref_authors
            or openalex_authors
            or []
        )

    # -------------------------
    # Venue
    # -------------------------
    merged["venue"] = (
        grobid.get("venue")
        or (crossref.get("venue") if crossref else None)
        or (openalex.get("venue") if openalex else None)
    )

    # -------------------------
    # Year
    # -------------------------
    merged["year"] = (
        grobid.get("year")
        or (crossref.get("year") if crossref else None)
        or (openalex.get("year") if openalex else None)
    )

    # -------------------------
    # References
    # -------------------------

    # References: GROBID > OpenAlex > Crossref
    refs = (
        grobid.get("references")
        or (openalex.get("references") if openalex else None)
        or (crossref.get("references") if crossref else None)
        or []
    )

    # If references are OpenAlex IDs, enrich them
    if refs and isinstance(refs[0], str) and refs[0].startswith("https://openalex.org/"):
        refs = enrich_openalex_references(refs)

    merged["references"] = refs

    return merged
