from dataclasses import dataclass

@dataclass
class ScoredDocument:
    doc_id: str
    score: float
 