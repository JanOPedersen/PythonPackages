"""
validators.py
Core normalization + validation utilities for the representation layer.

These functions are intentionally dependency-light and deterministic.
They are used across factories, merge rules, deduplication, and canonicalization.
"""

from __future__ import annotations

import re
import unicodedata
from datetime import datetime
from typing import Optional, Union


# ---------------------------------------------------------------------------
# DOI
# ---------------------------------------------------------------------------

_DOI_REGEX = re.compile(
    r"10\.\d{4,9}/[-._;()/:A-Za-z0-9]+$",
    re.IGNORECASE,
)

def normalize_doi(value: Optional[str]) -> Optional[str]:
    """
    Normalize a DOI into canonical form:
    - strip whitespace
    - remove URL prefixes
    - lowercase
    - validate format
    """
    if not value:
        return None

    v = value.strip()

    # Remove URL prefixes
    v = re.sub(r"^https?://(dx\.)?doi\.org/", "", v, flags=re.IGNORECASE)

    # Remove "doi:" prefix
    v = re.sub(r"^doi:\s*", "", v, flags=re.IGNORECASE)

    v = v.strip().lower()

    if _DOI_REGEX.match(v):
        return v

    return None


# ---------------------------------------------------------------------------
# ORCID
# ---------------------------------------------------------------------------

_ORCID_REGEX = re.compile(
    r"^(\d{4}-){3}\d{3}[\dX]$",
    re.IGNORECASE,
)

def normalize_orcid(value: Optional[str]) -> Optional[str]:
    """
    Normalize ORCID:
    - strip whitespace
    - remove URL prefix
    - uppercase X
    - validate checksum
    """
    if not value:
        return None

    v = value.strip()

    # Remove URL prefix
    v = re.sub(r"^https?://orcid\.org/", "", v, flags=re.IGNORECASE)

    v = v.upper()

    if not _ORCID_REGEX.match(v):
        return None

    # Checksum validation (ISO 7064 Mod 11-2)
    digits = v.replace("-", "")
    total = 0
    for char in digits[:-1]:
        total = (total + int(char)) * 2

    remainder = total % 11
    result = (12 - remainder) % 11
    check_digit = "X" if result == 10 else str(result)

    if digits[-1] == check_digit:
        return v

    return None


# ---------------------------------------------------------------------------
# arXiv ID
# ---------------------------------------------------------------------------

_ARXIV_REGEX = re.compile(
    r"^(arXiv:)?(\d{4}\.\d{4,5})(v\d+)?$",
    re.IGNORECASE,
)

def normalize_arxiv_id(value: Optional[str]) -> Optional[str]:
    """
    Normalize arXiv IDs:
    - remove 'arXiv:' prefix
    - lowercase
    - keep version if present
    """
    if not value:
        return None

    v = value.strip()

    m = _ARXIV_REGEX.match(v)
    if not m:
        return None

    base = m.group(2)
    version = m.group(3) or ""

    return f"{base}{version}".lower()


# ---------------------------------------------------------------------------
# ISBN
# ---------------------------------------------------------------------------

def normalize_isbn(value: Optional[str]) -> Optional[str]:
    """
    Normalize ISBN-10 or ISBN-13:
    - remove hyphens/spaces
    - uppercase X
    - validate checksum
    """
    if not value:
        return None

    v = re.sub(r"[-\s]", "", value).upper()

    if len(v) == 10:
        # ISBN-10 checksum
        if not re.match(r"^\d{9}[\dX]$", v):
            return None
        total = sum((10 - i) * (10 if c == "X" else int(c)) for i, c in enumerate(v))
        return v if total % 11 == 0 else None

    if len(v) == 13:
        # ISBN-13 checksum
        if not v.isdigit():
            return None
        total = sum((int(c) * (1 if i % 2 == 0 else 3)) for i, c in enumerate(v))
        return v if total % 10 == 0 else None

    return None


# ---------------------------------------------------------------------------
# ISSN
# ---------------------------------------------------------------------------

_ISSN_REGEX = re.compile(r"^\d{4}-\d{3}[\dX]$", re.IGNORECASE)

def normalize_issn(value: Optional[str]) -> Optional[str]:
    """
    Normalize ISSN:
    - enforce XXXX-XXXX format
    - validate checksum
    """
    if not value:
        return None

    v = value.strip().upper()

    if not _ISSN_REGEX.match(v):
        return None

    digits = v.replace("-", "")
    total = sum((8 - i) * (10 if c == "X" else int(c)) for i, c in enumerate(digits))
    return v if total % 11 == 0 else None


# ---------------------------------------------------------------------------
# Title normalization
# ---------------------------------------------------------------------------

def normalize_title(value: Optional[str]) -> Optional[str]:
    """
    Normalize titles for deduplication:
    - Unicode normalize
    - collapse whitespace
    - lowercase
    - strip punctuation at ends
    """
    if not value:
        return None

    v = unicodedata.normalize("NFKC", value)
    v = re.sub(r"\s+", " ", v).strip()
    v = v.strip(" .,:;!?").lower()

    return v or None


# ---------------------------------------------------------------------------
# Author name normalization
# ---------------------------------------------------------------------------

def normalize_author_name(value: Optional[str]) -> Optional[str]:
    """
    Normalize author names:
    - Unicode normalize
    - collapse whitespace
    - remove trailing commas
    - title-case (but preserve initials)
    """
    if not value:
        return None

    v = unicodedata.normalize("NFKC", value)
    v = re.sub(r"\s+", " ", v).strip().strip(",")

    # Preserve initials: "DOE, J." → "Doe, J."
    parts = v.split(" ")
    normalized = []
    for p in parts:
        if len(p) == 2 and p.endswith("."):
            normalized.append(p.upper())  # initials
        else:
            normalized.append(p.capitalize())

    return " ".join(normalized)


# ---------------------------------------------------------------------------
# Date parsing
# ---------------------------------------------------------------------------

_DATE_FORMATS = [
    "%Y",
    "%Y-%m",
    "%Y-%m-%d",
    "%d-%m-%Y",
    "%m/%d/%Y",
    "%Y/%m/%d",
]

def parse_date(value: Optional[str]) -> Optional[datetime]:
    """
    Parse dates from common formats.
    Returns a datetime or None.
    """
    if not value:
        return None

    v = value.strip()

    for fmt in _DATE_FORMATS:
        try:
            return datetime.strptime(v, fmt)
        except ValueError:
            continue

    return None


# ---------------------------------------------------------------------------
# URL normalization
# ---------------------------------------------------------------------------

def normalize_url(value: Optional[str]) -> Optional[str]:
    """
    Normalize URLs:
    - strip whitespace
    - ensure lowercase scheme + host
    """
    if not value:
        return None

    v = value.strip()

    # Basic sanity check
    if not re.match(r"^https?://", v, re.IGNORECASE):
        return None

    # Lowercase scheme + host
    parts = v.split("://", 1)
    scheme = parts[0].lower()
    rest = parts[1]

    # Lowercase host only
    if "/" in rest:
        host, path = rest.split("/", 1)
        return f"{scheme}://{host.lower()}/{path}"
    else:
        return f"{scheme}://{rest.lower()}"


# ---------------------------------------------------------------------------
# Email validation
# ---------------------------------------------------------------------------

_EMAIL_REGEX = re.compile(
    r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$"
)

def validate_email(value: Optional[str]) -> Optional[str]:
    if not value:
        return None

    v = value.strip()
    return v if _EMAIL_REGEX.match(v) else None


# ---------------------------------------------------------------------------
# Generic helpers
# ---------------------------------------------------------------------------

def empty_to_none(value: Optional[str]) -> Optional[str]:
    """
    Convert empty strings or whitespace to None.
    """
    if value is None:
        return None
    v = value.strip()
    return v if v else None
 