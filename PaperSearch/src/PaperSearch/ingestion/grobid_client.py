import requests
import os
from .utils import extract_doi, make_pdf_hash_doi, make_internal_doi
from PaperSearch.src.PaperSearch.utils.grobid_tei_parser import parse_tei

GROBID_BASE_URL = "http://localhost:8070"
base_url = GROBID_BASE_URL.rstrip("/")

def process_header(pdf_path: str) -> str:
    """
    Calls GROBID /api/processHeaderDocument to extract header metadata
    (title, authors, affiliations, abstract, publication info).
    """
    url = f"{base_url}/api/processHeaderDocument"

    headers = { "Accept": "application/xml" }

    with open(pdf_path, "rb") as f:
        files = {
            "input": (
                os.path.basename(pdf_path),
                f,
                "application/pdf"
            )
        }
        response = requests.post(url, headers=headers, files=files, timeout=30)

    if response.status_code != 200:
        raise RuntimeError(f"GROBID header extraction failed: {response.text}")

    return response.text

def process_fulltext(pdf_path: str) -> str:
    """
    Sends a PDF to GROBID and returns TEI XML as string.
    """
    url = f"{base_url}/api/processFulltextDocument"

    with open(pdf_path, "rb") as f:
        files = {"input": f}
        resp = requests.post(url, files=files, timeout=30)

    resp.raise_for_status()
    return resp.text

def grobid_search_pdf(pdf_path: str) -> dict:
    """
    Sends a PDF to GROBID and returns both header and fulltext TEI XML as strings.
    """
    doi = extract_doi(pdf_path)
    if doi is None:
        meta_data = parse_tei(process_fulltext(pdf_path))
        if meta_data["title"] and meta_data["authors"] and meta_data["year"]:
            doi = make_internal_doi(
                meta_data["title"],
                [a["name"] for a in meta_data["authors"]],
                str(meta_data["year"])
            )
        else:
            doi = make_pdf_hash_doi(pdf_path)

    return {"doi": doi, "header": process_header(pdf_path), "fulltext": process_fulltext(pdf_path)}
