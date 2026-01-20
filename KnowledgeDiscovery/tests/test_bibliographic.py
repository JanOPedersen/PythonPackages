import pytest
from representation.core.core_entities import Document, Person, Identifier, Venue
from representation.metadata.bibliographic import (
    normalize_title,
    normalize_authors,
    normalize_identifiers,
    infer_year_from_identifiers,
    infer_venue,
    process_bibliographic,
)


# ------------------------------------------------------------
# Title tests
# ------------------------------------------------------------

def test_normalize_title():
    doc = Document(id="1", title="  A Study on Something.  ")
    doc = normalize_title(doc)
    assert doc.title == "A Study on Something"


# ------------------------------------------------------------
# Author tests
# ------------------------------------------------------------

def test_normalize_authors_split_full_name():
    doc = Document(
        id="1",
        authors=[Person(given=None, family="John Doe")]
    )
    doc = normalize_authors(doc)
    assert doc.authors[0].given == "John"
    assert doc.authors[0].family == "Doe"


def test_normalize_authors_clean_whitespace():
    doc = Document(
        id="1",
        authors=[Person(given=" John ", family=" Doe ")]
    )
    doc = normalize_authors(doc)
    assert doc.authors[0].given == "John"
    assert doc.authors[0].family == "Doe"


# ------------------------------------------------------------
# Identifier tests
# ------------------------------------------------------------

def test_normalize_identifiers_deduplicate():
    doc = Document(
        id="1",
        identifiers=[
            Identifier(type="arxiv", value="2101.12345"),
            Identifier(type="arxiv", value="2101.12345"),
        ]
    )
    doc = normalize_identifiers(doc)
    assert len(doc.identifiers) == 1


# ------------------------------------------------------------
# Year inference tests
# ------------------------------------------------------------

def test_infer_year_from_arxiv_id():
    doc = Document(
        id="1",
        identifiers=[Identifier(type="arxiv", value="2101.12345")]
    )
    doc = infer_year_from_identifiers(doc)
    assert doc.year == 2021


def test_infer_year_does_not_override_existing():
    doc = Document(
        id="1",
        year=2019,
        identifiers=[Identifier(type="arxiv", value="2101.12345")]
    )
    doc = infer_year_from_identifiers(doc)
    assert doc.year == 2019


# ------------------------------------------------------------
# Venue inference tests
# ------------------------------------------------------------

def test_infer_venue_arxiv():
    doc = Document(
        id="1",
        identifiers=[Identifier(type="arxiv", value="2101.12345")]
    )
    doc = infer_venue(doc)
    assert doc.venue.name == "arXiv"
    assert doc.venue.type == "repository"


# ------------------------------------------------------------
# Pipeline tests
# ------------------------------------------------------------

def test_process_bibliographic_pipeline():
    doc = Document(
        id="1",
        title="  A Study on Something. ",
        authors=[Person(given=None, family="John Doe")],
        identifiers=[Identifier(type="arxiv", value="2101.12345")],
    )

    doc = process_bibliographic(doc)

    assert doc.title == "A Study on Something"
    assert doc.authors[0].given == "John"
    assert doc.authors[0].family == "Doe"
    assert doc.year == 2021
    assert doc.venue.name == "arXiv"
