from __future__ import annotations
import requests
import os

#class GrobidClient:
#    def __init__(self, base_url: str = "http://localhost:8070"):
#        self.base_url = base_url.rstrip("/")

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

def grobid_search_pdf(pdf_path: str) -> str:
    """
    Sends a PDF to GROBID and returns both header and fulltext TEI XML as strings.
    """
    return {"header:": process_header(pdf_path), "fulltext": process_fulltext(pdf_path)}
