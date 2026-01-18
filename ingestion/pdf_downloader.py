# pdf_downloader.py
import os
import re
import time
import json
import logging
from pathlib import Path
from typing import Optional

import requests

from ingestion.models import Paper

log = logging.getLogger(__name__)


# ---------- Helpers ----------

def _slugify(text: str, max_len: int = 80) -> str:
    text = text.strip().lower()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    text = re.sub(r"-+", "-", text).strip("-")
    return text[:max_len] or "paper"


def _safe_write_pdf(content: bytes, out_dir: Path, filename: str) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / filename
    with open(path, "wb") as f:
        f.write(content)
    return path


def _http_get(url: str, timeout: int = 20) -> Optional[requests.Response]:
    try:
        resp = requests.get(url, timeout=timeout, allow_redirects=True)
        if resp.status_code == 200 and resp.headers.get("content-type", "").startswith("application/pdf"):
            return resp
        return None
    except Exception as e:
        log.warning(f"HTTP GET failed for {url}: {e}")
        return None


# ---------- 1. arXiv ----------

def _extract_arxiv_id(paper: Paper) -> Optional[str]:
    # from extra
    arxiv_id = paper.extra.get("arxiv_id")
    if arxiv_id:
        return arxiv_id

    # from DOI like 10.48550/arXiv.XXXX
    if paper.doi and "arxiv." in paper.doi.lower():
        return paper.doi.split("arxiv.", 1)[1]

    # from title/extra/url patterns (optional, heuristic)
    url = paper.extra.get("arxiv_url") or paper.extra.get("url")
    if url and "arxiv.org" in url:
        m = re.search(r"arxiv\.org/(abs|pdf)/([0-9]+\.[0-9]+)", url)
        if m:
            return m.group(2)

    return None


def download_from_arxiv(paper: Paper, out_dir: Path) -> Optional[Path]:
    arxiv_id = _extract_arxiv_id(paper)
    if not arxiv_id:
        return None

    pdf_url = f"https://arxiv.org/pdf/{arxiv_id}.pdf"
    resp = _http_get(pdf_url)
    if not resp:
        return None

    filename = f"arxiv-{arxiv_id}.pdf"
    path = _safe_write_pdf(resp.content, out_dir, filename)
    log.info(f"Downloaded arXiv PDF for {paper.title!r} → {path}")
    return path


# ---------- 2. OpenAlex ----------

OPENALEX_BASE = "https://api.openalex.org/works"


def _openalex_get_work_by_doi(doi: str) -> Optional[dict]:
    url = f"{OPENALEX_BASE}/https://doi.org/{doi}"
    try:
        r = requests.get(url, timeout=20)
        if r.status_code == 200:
            return r.json()
    except Exception as e:
        log.warning(f"OpenAlex DOI lookup failed: {e}")
    return None


def _openalex_search_by_title(title: str) -> Optional[dict]:
    params = {"search": title, "per-page": 1}
    try:
        r = requests.get(OPENALEX_BASE, params=params, timeout=20)
        if r.status_code == 200:
            data = r.json()
            if "results" in data and data["results"]:
                return data["results"][0]
    except Exception as e:
        log.warning(f"OpenAlex title search failed: {e}")
    return None


def _openalex_best_pdf_url(work: dict) -> Optional[str]:
    # OpenAlex "best_oa_location" often has a PDF URL
    loc = work.get("best_oa_location") or {}
    url = loc.get("url_for_pdf") or loc.get("url")
    return url


def download_from_openalex(paper: Paper, out_dir: Path) -> Optional[Path]:
    work = None

    if paper.doi:
        work = _openalex_get_work_by_doi(paper.doi)

    if not work and paper.title:
        work = _openalex_search_by_title(paper.title)

    if not work:
        return None

    pdf_url = _openalex_best_pdf_url(work)
    if not pdf_url:
        return None

    resp = _http_get(pdf_url)
    if not resp:
        return None

    slug = _slugify(paper.title)
    filename = f"openalex-{slug}.pdf"
    path = _safe_write_pdf(resp.content, out_dir, filename)
    log.info(f"Downloaded PDF via OpenAlex for {paper.title!r} → {path}")
    return path


# ---------- 3. Semantic Scholar ----------

S2_BASE = "https://api.semanticscholar.org/graph/v1/paper"


def _s2_get_paper_by_doi(doi: str) -> Optional[dict]:
    url = f"{S2_BASE}/DOI:{doi}"
    params = {"fields": "title,openAccessPdf,url"}
    try:
        r = requests.get(url, params=params, timeout=20)
        if r.status_code == 200:
            return r.json()
    except Exception as e:
        log.warning(f"Semantic Scholar DOI lookup failed: {e}")
    return None


def _s2_search_by_title(title: str) -> Optional[dict]:
    # Semantic Scholar search API (simple version)
    url = "https://api.semanticscholar.org/graph/v1/paper/search"
    params = {"query": title, "limit": 1, "fields": "title,openAccessPdf,url"}
    try:
        r = requests.get(url, params=params, timeout=20)
        if r.status_code == 200:
            data = r.json()
            if "data" in data and data["data"]:
                return data["data"][0]
    except Exception as e:
        log.warning(f"Semantic Scholar title search failed: {e}")
    return None


def _s2_best_pdf_url(paper_json: dict) -> Optional[str]:
    oa = paper_json.get("openAccessPdf") or {}
    return oa.get("url")


def download_from_semantic_scholar(paper: Paper, out_dir: Path) -> Optional[Path]:
    s2 = None

    if paper.doi:
        s2 = _s2_get_paper_by_doi(paper.doi)

    if not s2 and paper.title:
        s2 = _s2_search_by_title(paper.title)

    if not s2:
        return None

    pdf_url = _s2_best_pdf_url(s2)
    if not pdf_url:
        return None

    resp = _http_get(pdf_url)
    if not resp:
        return None

    slug = _slugify(paper.title)
    filename = f"s2-{slug}.pdf"
    path = _safe_write_pdf(resp.content, out_dir, filename)
    log.info(f"Downloaded PDF via Semantic Scholar for {paper.title!r} → {path}")
    return path


# ---------- Orchestrator ----------

def download_pdf_for_paper(paper: Paper, out_dir: str | Path) -> Paper:
    """
    Try arXiv → OpenAlex → Semantic Scholar.
    If successful, set paper.pdf_path and return updated paper.
    """
    out_dir = Path(out_dir)

    # 1. arXiv
    path = download_from_arxiv(paper, out_dir)
    if path:
        paper.pdf_path = str(path)
        return paper

    # 2. OpenAlex
    path = download_from_openalex(paper, out_dir)
    if path:
        paper.pdf_path = str(path)
        return paper

    # 3. Semantic Scholar
    path = download_from_semantic_scholar(paper, out_dir)
    if path:
        paper.pdf_path = str(path)
        return paper

    log.info(f"No PDF found for {paper.title!r}")
    return paper
