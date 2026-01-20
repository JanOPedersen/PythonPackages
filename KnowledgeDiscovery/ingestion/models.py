# ingestion/models.py
from dataclasses import dataclass, field
from typing import List, Optional, Dict


@dataclass
class Paper:
    paper_id: str
    doi: Optional[str]
    title: str
    abstract: Optional[str]
    authors: List[str]
    year: Optional[int]
    venue: Optional[str]
    pdf_path: Optional[str]
    full_text: Optional[str]
    references: List[str]  # DOIs or internal IDs
    source: str
    user_tags: List[str] = field(default_factory=list)
    projects: List[str] = field(default_factory=list)
    extra: Dict[str, str] = field(default_factory=dict)
