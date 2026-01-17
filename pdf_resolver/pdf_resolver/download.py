# pdf_resolver/download.py
import os
import pathlib
import requests
from typing import Optional

def ensure_dir(path: str) -> None:
    pathlib.Path(path).mkdir(parents=True, exist_ok=True)

def download_pdf(url: str, dest_dir: str, filename: str) -> Optional[str]:
    ensure_dir(dest_dir)
    safe_name = "".join(c for c in filename if c.isalnum() or c in "._-") or "paper"
    path = os.path.join(dest_dir, safe_name + ".pdf")
    resp = requests.get(url, timeout=30)
    if resp.status_code != 200 or "application/pdf" not in resp.headers.get("Content-Type", ""):
        return None
    with open(path, "wb") as f:
        f.write(resp.content)
    return path
