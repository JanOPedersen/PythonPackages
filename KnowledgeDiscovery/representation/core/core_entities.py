from __future__ import annotations
from pydantic import BaseModel, Field
from typing import Optional, Literal, List, Dict, Any 

# ------------------------------------------------------------
# Identifier
# ------------------------------------------------------------

class Identifier(BaseModel):
    type: Literal["doi", "arxiv", "isbn", "openalex", "s2", "internal"]
    value: str


# ------------------------------------------------------------
# Person
# ------------------------------------------------------------

class Person(BaseModel):
    given: Optional[str] = None
    family: Optional[str] = None
    orcid: Optional[str] = None
    affiliation: Optional[str] = None


# ------------------------------------------------------------
# Venue
# ------------------------------------------------------------

class Venue(BaseModel):
    name: str
    type: Literal["journal", "conference", "workshop", "book", "repository"]
    publisher: Optional[str] = None


# ------------------------------------------------------------
# Reference
# ------------------------------------------------------------

class Reference(BaseModel):
    title: Optional[str] = None
    authors: Optional[List[Person]] = None
    year: Optional[int] = None
    identifiers: Optional[List[Identifier]] = None


# ------------------------------------------------------------
# File
# ------------------------------------------------------------

class File(BaseModel):
    path: str
    mime_type: Optional[str] = None
    size_bytes: Optional[int] = None
    checksum_md5: Optional[str] = None
    checksum_sha256: Optional[str] = None


# ------------------------------------------------------------
# Source
# ------------------------------------------------------------

class Source(BaseModel):
    origin: Literal[
        "arxiv",
        "crossref",
        "openalex",
        "semantic_scholar",
        "local_pdf",
        "zotero",
        "grobid",
        "xmp",
    ]
    retrieved_at: Optional[str] = None  # ISO timestamp
    url: Optional[str] = None


# ------------------------------------------------------------
# IngestionEvent
# ------------------------------------------------------------

class IngestionEvent(BaseModel):
    stage: Literal["download", "parse", "extract", "enrich", "store"]
    timestamp: str  # ISO timestamp
    source: Source
    notes: Optional[str] = None


# ------------------------------------------------------------
# Document (Core Entity)
# ------------------------------------------------------------

class Document(BaseModel):
    id: str
    identifiers: List[Identifier] = Field(default_factory=list)

    title: Optional[str] = None
    abstract: Optional[str] = None
    authors: Optional[List[Person]] = None
    venue: Optional[Venue] = None
    year: Optional[int] = None
    references: Optional[List[Reference]] = None

    files: List[File] = Field(default_factory=list)
    ingestion_events: List[IngestionEvent] = Field(default_factory=list)

    # NEW FIELD 
    enrichment: Optional[Dict[str, Any]] = Field(default_factory=dict)
