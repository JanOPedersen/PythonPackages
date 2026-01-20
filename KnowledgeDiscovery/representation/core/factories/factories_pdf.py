from __future__ import annotations
from representation.core.core_entities import Document
from .grobid_client import GrobidClient
from .grobid_tei_parser import parse_tei
from .doi_pipeline import extract_doi
from lxml import etree

def from_pdf(pdf_path: str, grobid=None) -> Document:
    grobid = grobid or GrobidClient()

    tei_xml = grobid.process_fulltext(pdf_path)
    meta = parse_tei(tei_xml)

    # Parse TEI root for DOI extraction
    root = etree.fromstring(tei_xml.encode("utf-8"))
    doi = extract_doi(pdf_path, tei_root=root)

    return Document(
        id=doi or f"pdf:{pdf_path}",
        title=meta["title"],
        authors=meta["authors"],
        abstract=meta["abstract"],
        venue=meta["venue"],
        year=meta["year"],
        references=meta["references"],
        identifiers=[{"type": "doi", "value": doi}] if doi else [],
        files=[pdf_path],
        ingestion_events=[{"source": "grobid", "path": pdf_path}],
    )
