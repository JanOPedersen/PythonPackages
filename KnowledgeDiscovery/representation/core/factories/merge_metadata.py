def merge_metadata_old(grobid: dict, crossref: dict | None, openalex: dict | None) -> dict:
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
    # Abstract priority:
    # 1. GROBID (best quality)
    # 2. OpenAlex (fallback)
    # 3. Crossref (rarely present)
    merged["abstract"] = (
        grobid.get("abstract")
        or (openalex.get("abstract") if openalex else None)
        or (crossref.get("abstract") if crossref else None)
    )


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


def merge_metadata(grobid, crossref, openalex):
    merged = {}

    # Title
    merged["title"] = (
        grobid.get("title")
        or crossref.get("title") if crossref else None
        or openalex.get("title") if openalex else None
    )

    # Authors: GROBID wins
    merged["authors"] = (
        grobid.get("authors")
        or (crossref.get("authors") if crossref else None)
        or (openalex.get("authors") if openalex else None)
        or []
    )

    # Abstract: GROBID header wins
    merged["abstract"] = (
        grobid.get("abstract")
        or (crossref.get("abstract") if crossref else None)
        or (openalex.get("abstract") if openalex else None)
    )

    # Venue
    merged["venue"] = (
        grobid.get("venue")
        or (crossref.get("venue") if crossref else None)
        or (openalex.get("venue") if openalex else None)
    )

    # Year
    merged["year"] = (
        grobid.get("year")
        or (crossref.get("year") if crossref else None)
        or (openalex.get("year") if openalex else None)
    )

    # References: OpenAlex > GROBID > Crossref
    ''' 
    merged["references"] = (
        (openalex.get("references") if openalex else None)
        or grobid.get("references")
        or (crossref.get("references") if crossref else None)
        or []
    )
    '''

    merged["references"] = grobid.get("references", [])

    # Enrichment
    if openalex:
        merged["concepts"] = openalex.get("concepts")
        merged["citations"] = openalex.get("citations")
        merged["related_works"] = openalex.get("related_works")

    return merged
