from __future__ import annotations
from typing import List, Optional, Dict
from lxml import etree

def extract_doi_from_tei(root) -> str | None:
    el = root.find(".//idno[@type='DOI']")
    if el is not None and el.text:
        return el.text.strip()
    return None

def parse_tei(tei_xml: str) -> Dict:
    """
    Extracts structured metadata from GROBID TEI XML.
    Returns a dict with:
    - title
    - authors (list of dicts)
    - affiliations (list)
    - abstract
    - venue
    - year
    - references (list)
    """
    root = etree.fromstring(tei_xml.encode("utf-8"))

    # -------------------------
    # Title
    # -------------------------
    title_el = root.find(".//titleStmt/title")
    title = title_el.text.strip() if title_el is not None else None

    # -------------------------
    # Authors + affiliations
    # -------------------------
    authors = []
    for author_el in root.findall(".//author"):
        name_el = author_el.find(".//persName")
        if name_el is not None:
            full_name = " ".join(
                filter(None, [
                    name_el.findtext("forename"),
                    name_el.findtext("surname")
                ])
            )
        else:
            full_name = None

        aff_el = author_el.find(".//affiliation/orgName")
        affiliation = aff_el.text.strip() if aff_el is not None else None

        authors.append({
            "name": full_name,
            "affiliation": affiliation,
        })

    # -------------------------
    # Abstract
    # -------------------------
    abstract_el = root.find(".//abstract")
    abstract = "".join(abstract_el.itertext()).strip() if abstract_el is not None else None

    # -------------------------
    # Venue + publication date
    # -------------------------
    venue_el = root.find(".//sourceDesc/biblStruct/monogr/title")
    venue = venue_el.text.strip() if venue_el is not None else None

    date_el = root.find(".//sourceDesc/biblStruct/monogr/imprint/date")
    year = int(date_el.get("when")[:4]) if date_el is not None and date_el.get("when") else None

    # -------------------------
    # References
    # -------------------------
    references = []
    for ref in root.findall(".//listBibl/biblStruct"):
        ref_title_el = ref.find(".//title")
        ref_title = ref_title_el.text.strip() if ref_title_el is not None else None
        references.append({"title": ref_title})

    return {
        "title": title,
        "authors": authors,
        "abstract": abstract,
        "venue": venue,
        "year": year,
        "references": references,
    }
