from __future__ import annotations
from ..core_entities import Document
from .grobid_client import GrobidClient
from .grobid_tei_parser import parse_tei
from .doi_pipeline import extract_doi
from lxml import etree
from .factories_crossref import from_doi as crossref_from_doi
from .factories_openalex import from_doi as openalex_from_doi
from .merge_metadata import merge_metadata
from datetime import datetime 
from ..core_entities import ( Document, Author, Person, Venue, File, Source, IngestionEvent )

def from_pdf(pdf_path: str, grobid=None) -> Document:
    grobid = grobid or GrobidClient()

    # 1. GROBID
    tei_header = grobid.process_header(pdf_path)
    print(tei_header)

    tei_fulltext = grobid.process_fulltext(pdf_path)

    header_meta = parse_tei(tei_header)
    fulltext_meta = parse_tei(tei_fulltext)

    # merge: header wins for abstract, title, authors
    grobid_meta = {**fulltext_meta, **header_meta}

    root = etree.fromstring(tei_header.encode("utf-8"))

    # 2. DOI
    doi = extract_doi(pdf_path, tei_root=root)

    # 3. Crossref
    crossref_meta = crossref_from_doi(doi) if doi else None

    # 4. OpenAlex
    openalex_meta = openalex_from_doi(doi) if doi else None

    # 5. Merge
    merged = merge_metadata(grobid_meta, crossref_meta, openalex_meta)

    # 6. Convert authors
    authors = []
    for a in merged.get("authors", []):
        authors.append(
            Person(
                given=a.get("given"),
                family=a.get("family"),
                orcid=a.get("orcid") if isinstance(a.get("orcid"), str) else None,
                affiliation=a.get("affiliation") if isinstance(a.get("affiliation"), str) else None
            )
        )

    # 7. Venue
    venue = None
    if merged.get("venue"):
        venue = Venue(
            name=merged["venue"],
            type="journal"  # or "conference" if you prefer
        )


    # 8. Files
    files = [File(path=pdf_path)]

    # 9. Ingestion event
    ingestion_events = [
        IngestionEvent(
            stage="extract",
            timestamp=datetime.utcnow().isoformat(),
            source=Source(
                name="grobid",
                origin="grobid"   # or "pipeline", or "service", depending on your design
            )
        )
    ]

    # 10. Build Document
    return Document(
        id=doi or f"pdf:{pdf_path}",
        identifiers=[{"type": "doi", "value": doi}] if doi else [],
        title=merged.get("title"),
        abstract=merged.get("abstract"),
        authors=authors,
        venue=venue,
        year=merged.get("year"),
        references=merged.get("references"),
        files=files,
        ingestion_events=ingestion_events,
    )
