from dataclasses import dataclass 

@dataclass
class NormalizedWork:
    work_id: str
    doi: str | None
    arxiv_id: str | None
    title: str | None
    authors: list[dict]
    year: int | None
    source_metadata: dict   # optional: keep raw sources for debugging
