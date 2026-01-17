# pdf_resolver/resolver_types.py
from dataclasses import dataclass
from typing import Optional

@dataclass
class PDFResolutionResult:
    paper_id: str
    pdf_url: Optional[str]
    local_path: Optional[str]
    extracted_text: Optional[str]
    strategy: Optional[str]
    quality_score: Optional[float]
    error: Optional[str] = None
