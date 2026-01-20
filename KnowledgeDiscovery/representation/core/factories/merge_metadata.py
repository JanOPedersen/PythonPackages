def merge_metadata(grobid: dict, crossref: dict | None, openalex: dict | None) -> dict:
    """
    Priority:
    1. Crossref (publisher-verified)
    2. GROBID (PDF-derived)
    3. OpenAlex (enrichment)
    """

    merged = {}

    # Title
    merged["title"] = crossref.get("title") if crossref else grobid.get("title")

    # Authors
    merged["authors"] = crossref.get("authors") if crossref else grobid.get("authors")

    # Abstract
    merged["abstract"] = grobid.get("abstract")

    # Venue
    merged["venue"] = crossref.get("venue") if crossref else grobid.get("venue")

    # Year
    merged["year"] = crossref.get("year") if crossref else grobid.get("year")

    # References (GROBID gives structured refs, OpenAlex gives IDs)
    merged["references"] = grobid.get("references", [])

    # Enrichment
    if openalex:
        merged["concepts"] = openalex.get("concepts")
        merged["citations"] = openalex.get("citations")
        merged["related_works"] = openalex.get("related_works")

    return merged
