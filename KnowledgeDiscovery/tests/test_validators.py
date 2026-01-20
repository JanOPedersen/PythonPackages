import pytest
from representation.core.validators import (
    normalize_doi,
    normalize_orcid,
    normalize_arxiv_id,
    normalize_isbn,
    normalize_issn,
    normalize_title,
    normalize_author_name,
    parse_date,
    normalize_url,
    validate_email,
    empty_to_none,
)


# ---------------------------------------------------------------------------
# DOI
# ---------------------------------------------------------------------------

def test_normalize_doi_valid():
    assert normalize_doi("10.1000/xyz") == "10.1000/xyz"
    assert normalize_doi(" https://doi.org/10.1000/xyz ") == "10.1000/xyz"
    assert normalize_doi("DOI:10.1000/xyz") == "10.1000/xyz"


def test_normalize_doi_invalid():
    assert normalize_doi("not-a-doi") is None
    assert normalize_doi("10.1000") is None
    assert normalize_doi("") is None
    assert normalize_doi(None) is None


# ---------------------------------------------------------------------------
# ORCID
# ---------------------------------------------------------------------------

def test_normalize_orcid_valid():
    assert normalize_orcid("0000-0002-1825-0097") == "0000-0002-1825-0097"
    assert normalize_orcid("https://orcid.org/0000-0002-1825-0097") == "0000-0002-1825-0097"


def test_normalize_orcid_invalid():
    assert normalize_orcid("0000-0002-1825-009X") is None  # wrong checksum
    assert normalize_orcid("not-an-orcid") is None
    assert normalize_orcid("") is None
    assert normalize_orcid(None) is None


# ---------------------------------------------------------------------------
# arXiv
# ---------------------------------------------------------------------------

def test_normalize_arxiv_id_valid():
    assert normalize_arxiv_id("arXiv:2101.12345") == "2101.12345"
    assert normalize_arxiv_id("2101.12345v2") == "2101.12345v2"
    assert normalize_arxiv_id(" 2101.12345 ") == "2101.12345"


def test_normalize_arxiv_id_invalid():
    assert normalize_arxiv_id("not-arxiv") is None
    assert normalize_arxiv_id("2101.12") is None
    assert normalize_arxiv_id(None) is None


# ---------------------------------------------------------------------------
# ISBN
# ---------------------------------------------------------------------------

def test_normalize_isbn_valid():
    assert normalize_isbn("0-306-40615-2") == "0306406152"  # ISBN-10
    assert normalize_isbn("978-3-16-148410-0") == "9783161484100"  # ISBN-13


def test_normalize_isbn_invalid():
    assert normalize_isbn("1234567890") is None  # wrong checksum
    assert normalize_isbn("not-an-isbn") is None
    assert normalize_isbn(None) is None


# ---------------------------------------------------------------------------
# ISSN
# ---------------------------------------------------------------------------

def test_normalize_issn_valid():
    assert normalize_issn("0378-5955") == "0378-5955"
    assert normalize_issn("2434-561X") == "2434-561X"


def test_normalize_issn_invalid():
    assert normalize_issn("0378-5954") is None  # wrong checksum
    assert normalize_issn("not-an-issn") is None
    assert normalize_issn(None) is None


# ---------------------------------------------------------------------------
# Title normalization
# ---------------------------------------------------------------------------

def test_normalize_title():
    assert normalize_title("  Deep   Learning: An Overview  ") == "deep learning: an overview".strip(" .,:;!?")
    assert normalize_title("Deep Learning!") == "deep learning"
    assert normalize_title(None) is None


# ---------------------------------------------------------------------------
# Author name normalization
# ---------------------------------------------------------------------------

def test_normalize_author_name():
    assert normalize_author_name("DOE, J.") == "Doe, J."
    assert normalize_author_name("  john   doe ") == "John Doe"
    assert normalize_author_name(None) is None


# ---------------------------------------------------------------------------
# Date parsing
# ---------------------------------------------------------------------------

def test_parse_date_valid():
    assert parse_date("2020").year == 2020
    assert parse_date("2020-05").month == 5
    assert parse_date("2020-05-17").day == 17


def test_parse_date_invalid():
    assert parse_date("not-a-date") is None
    assert parse_date(None) is None


# ---------------------------------------------------------------------------
# URL normalization
# ---------------------------------------------------------------------------

def test_normalize_url_valid():
    assert normalize_url("HTTP://Example.com/Path") == "http://example.com/Path"
    assert normalize_url("https://example.com") == "https://example.com"


def test_normalize_url_invalid():
    assert normalize_url("example.com") is None
    assert normalize_url("ftp://example.com") is None
    assert normalize_url(None) is None


# ---------------------------------------------------------------------------
# Email validation
# ---------------------------------------------------------------------------

def test_validate_email():
    assert validate_email("test@example.com") == "test@example.com"
    assert validate_email("invalid-email") is None
    assert validate_email(None) is None


# ----------------------------------------------------------------