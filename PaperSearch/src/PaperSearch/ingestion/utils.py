import re
import hashlib
import uuid
from PaperSearch.src.PaperSearch.utils.doi_extractor import extract_doi_from_pdf_text, extract_doi_from_xmp
from PaperSearch.src.PaperSearch.utils.grobid_tei_parser import extract_doi_from_tei, parse_tei

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

def make_pdf_hash_doi(pdf_path: str) -> str:
    """
    Generate a stable internal DOI based on the SHA-256 hash of the PDF file.
    Uses the reserved 10.0000 prefix to avoid collisions with real DOIs.
    """
    sha256 = hashlib.sha256()

    with open(pdf_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256.update(chunk)

    digest = sha256.hexdigest()
    return f"10.0000/pdf-{digest}"

def make_internal_doi(title, authors, year):
    fingerprint = f"{title}|{','.join(authors)}|{year}"
    h = hashlib.sha1(fingerprint.encode("utf-8")).hexdigest()
    return f"10.0000/{h}"

def extract_doi(pdf_path: str, tei_root=None) -> str | None:
    """
    Multi-stage DOI extraction:
    1. GROBID TEI
    2. PDF text
    3. XMP metadata
    """

    # 1. Try GROBID TEI
    if tei_root is not None:
        doi = extract_doi_from_tei(tei_root)
        if doi:
            return doi

    # 2. Try PDF text
    doi = extract_doi_from_pdf_text(pdf_path)
    if doi:
        return doi

    # 3. Try XMP metadata
    doi = extract_doi_from_xmp(pdf_path)
    if doi:
        return doi

    return None
