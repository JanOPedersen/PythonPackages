import pytest
from representation.core.factories import from_arxiv, from_pdf
from representation.core.core_entities import Document, File, Identifier, Person


# ------------------------------------------------------------
# arXiv Tests
# ------------------------------------------------------------

def test_from_arxiv_basic():
    raw = {
        "arxiv_id": "2101.12345",
        "title": "  A Study on Something Interesting ",
        "authors": ["John Doe", "Jane Smith"],
        "summary": "This paper explores something.",
        "published": "2021-01-15",
        "link": "https://arxiv.org/abs/2101.12345",
    }

    doc = from_arxiv(raw)

    assert isinstance(doc, Document)
    assert doc.id == "2101.12345"
    assert doc.title == "A Study on Something Interesting"
    assert doc.abstract == "This paper explores something."
    assert doc.year == 2021

    # Identifiers
    assert any(i.type == "arxiv" for i in doc.identifiers)

    # Authors
    assert len(doc.authors) == 2
    assert isinstance(doc.authors[0], Person)
    assert doc.authors[0].family == "Doe"
    assert doc.authors[1].family == "Smith"


def test_from_arxiv_missing_fields():
    raw = {
        "id": "9999.99999",
        "title": None,
        "authors": [],
        "summary": None,
        "published": None,
    }

    doc = from_arxiv(raw)

    assert doc.id == "9999.99999"
    assert doc.title is None
    assert doc.abstract is None
    assert doc.year is None
    assert doc.authors == []


# ------------------------------------------------------------
# PDF Tests
# ------------------------------------------------------------

def test_from_pdf_basic():
    meta = {
        "mime_type": "application/pdf",
        "file_size": 204800,
        "md5": "abc123",
        "sha256": "deadbeef",
    }

    f = from_pdf("paper.pdf", meta)

    assert isinstance(f, File)
    assert f.path == "paper.pdf"
    assert f.mime_type == "application/pdf"
    assert f.size_bytes == 204800
    assert f.checksum_md5 == "abc123"
    assert f.checksum_sha256 == "deadbeef"


def test_from_pdf_missing_fields():
    meta = {}

    f = from_pdf("paper.pdf", meta)

    assert f.mime_type is None
    assert f.size_bytes is None
    assert f.checksum_md5 is None
    assert f.checksum_sha256 is None
