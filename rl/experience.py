# rl/experience.py
from dataclasses import dataclass, field
from typing import Any, Optional

@dataclass
class ExperienceRecord:
    paper_id: str
    title: str
    authors: list[str]
    year: Optional[int]
    venue: Optional[str]
    abstract: Optional[str]
    pdf_url: Optional[str]
    local_pdf_path: Optional[str]
    extracted_text: Optional[str]
    llm_summary: Optional[str]
    tags: list[str]
    reward: Optional[float] = None
    metadata: dict[str, Any] = field(default_factory=dict)
