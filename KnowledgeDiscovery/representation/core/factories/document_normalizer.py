class NormalizedDocument:
    def __init__(self, grobid_doc):
        self.doc_id = grobid_doc.id
        self.title = grobid_doc.title or ""
        self.abstract = grobid_doc.abstract or ""
        self.year = grobid_doc.year
        self.venue = getattr(grobid_doc.venue, "name", None)

    def __repr__(self):
        return f"Document({self.doc_id}, title={self.title[:60]!r})"
