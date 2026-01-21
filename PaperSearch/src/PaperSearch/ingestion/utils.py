import re

def canonicalise_doi(raw: str) -> str:
    """
    Convert any DOI-like string into a canonical bare DOI.
    """
    if raw is None:
        return None

    raw = raw.strip()

    # Remove URL prefixes
    raw = re.sub(r'^https?://(dx\.)?doi\.org/', '', raw, flags=re.IGNORECASE)

    # Remove leading "doi:" or "DOI "
    raw = re.sub(r'^doi:\s*', '', raw, flags=re.IGNORECASE)
    raw = re.sub(r'^doi\s+', '', raw, flags=re.IGNORECASE)

    # Normalise case
    return raw.lower()
