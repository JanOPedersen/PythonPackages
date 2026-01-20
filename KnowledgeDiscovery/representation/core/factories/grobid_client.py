from __future__ import annotations
import requests
from typing import Optional

class GrobidClient:
    def __init__(self, base_url: str = "http://localhost:8070"):
        self.base_url = base_url.rstrip("/")

    def process_fulltext(self, pdf_path: str) -> str:
        """
        Sends a PDF to GROBID and returns TEI XML as string.
        """
        url = f"{self.base_url}/api/processFulltextDocument"

        with open(pdf_path, "rb") as f:
            files = {"input": f}
            resp = requests.post(url, files=files, timeout=30)

        resp.raise_for_status()
        return resp.text
