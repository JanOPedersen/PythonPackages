from typing import Protocol, List, Tuple

class TextIndex(Protocol):
    def add(self, doc_id: str, text: str) -> None:
        ...

    def search(self, query: str, k: int = 20) -> List[Tuple[str, float]]:
        ...
 