class NormalizedDocument:
    def __init__(self, doc):
        self.doc_id = doc.id
        self.title = doc.title or ""
        self.abstract = doc.abstract or ""
        self.authors = [
            f"{a.given or ''} {a.family or ''}".strip()
            for a in (doc.authors or [])
        ]
        self.references = doc.references or []

    @classmethod
    def from_openalex(cls, item):
        doc_id = item.get("id")
        title = item.get("title")
        abstract = item.get("abstract_inverted_index")
        if abstract:
            # Convert OpenAlex inverted index to normal text
            abstract = " ".join(
                word for word, positions in sorted(
                    ((w, pos[0]) for w, pos in abstract.items()),
                    key=lambda x: x[1]
                )
            )

        authors = [
            a["author"]["display_name"]
            for a in item.get("authorships", [])
        ]

        year = item.get("publication_year")
        venue = item.get("host_venue", {}).get("display_name")

        return cls(doc_id, title, abstract, authors, year, venue)

    def text(self):
        parts = [
            self.title,
            self.abstract,
            " ".join(self.authors),
            " ".join(r.get("title", "") for r in self.references),
        ]
        return " ".join(p for p in parts if p).strip()

