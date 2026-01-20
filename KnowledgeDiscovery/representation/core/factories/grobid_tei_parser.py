from __future__ import annotations
from typing import List, Optional, Dict

from sympy import root
from lxml import etree

NS = {"tei": "http://www.tei-c.org/ns/1.0"}

def extract_doi_from_tei(root) -> str | None:
    el = root.find(".//idno[@type='DOI']")
    if el is not None and el.text:
        return el.text.strip()
    return None

def parse_tei_authors(root):
    authors = []

    for author_el in root.xpath(".//tei:author", namespaces=NS):
        person = {
            "given": None,
            "family": None,
            "orcid": None,
            "affiliation": None,
            "email": None,
        }

        # ORCID
        orcid_el = author_el.xpath(".//tei:idno[@type='ORCID']", namespaces=NS)
        if orcid_el:
            person["orcid"] = orcid_el[0].text

        # Email
        email_el = author_el.xpath(".//tei:email", namespaces=NS)
        if email_el:
            person["email"] = email_el[0].text

        # Names
        pers = author_el.xpath(".//tei:persName", namespaces=NS)
        if pers:
            pers = pers[0]

            # Collect all forenames
            forenames = pers.xpath("./tei:forename", namespaces=NS)
            if forenames:
                # Join first + middle names
                person["given"] = " ".join([fn.text for fn in forenames if fn.text])

            # Surname
            surname = pers.xpath("./tei:surname", namespaces=NS)
            if surname and surname[0].text:
                person["family"] = surname[0].text

            # Fallback: <name>John Doe</name>
            if not person["given"] and not person["family"]:
                name_el = pers.xpath("./tei:name", namespaces=NS)
                if name_el and name_el[0].text:
                    full = name_el[0].text.strip()
                    parts = full.split()
                    if len(parts) > 1:
                        person["given"] = " ".join(parts[:-1])
                        person["family"] = parts[-1]
                    else:
                        person["family"] = full

        # Affiliation (stringified)
        aff = author_el.xpath(".//tei:affiliation", namespaces=NS)
        if aff:
            # Extract institution name if present
            inst = aff[0].xpath(".//tei:orgName[@type='institution']", namespaces=NS)
            if inst and inst[0].text:
                person["affiliation"] = inst[0].text
            else:
                # fallback: any orgName
                org = aff[0].xpath(".//tei:orgName", namespaces=NS)
                if org and org[0].text:
                    person["affiliation"] = org[0].text

        authors.append(person)

    return authors


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
    authors = parse_tei_authors(root)

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
