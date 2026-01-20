from __future__ import annotations
from .doi_extractor import extract_doi_from_pdf_text, extract_doi_from_xmp
from .grobid_tei_parser import extract_doi_from_tei

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
