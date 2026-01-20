from __future__ import annotations
import re
import fitz  # PyMuPDF

DOI_REGEX = re.compile(
    r"10\.\d{4,9}/[-._;()/:A-Z0-9]+",
    re.IGNORECASE
)

def extract_doi_from_pdf_text(path: str) -> str | None:
    """
    Extract DOI from PDF text using regex.
    Works even when GROBID fails.
    """
    try:
        doc = fitz.open(path)
        text = "\n".join(page.get_text() for page in doc)
    except Exception:
        return None

    match = DOI_REGEX.search(text)
    return match.group(0) if match else None

def extract_doi_from_xmp(path: str) -> str | None:
    """
    Extract DOI from PDF XMP metadata if present.
    """
    try:
        doc = fitz.open(path)
        xmp = doc.metadata or {}
    except Exception:
        return None

    for key, value in xmp.items():
        if not isinstance(value, str):
            continue
        match = DOI_REGEX.search(value)
        if match:
            return match.group(0)

    return None
