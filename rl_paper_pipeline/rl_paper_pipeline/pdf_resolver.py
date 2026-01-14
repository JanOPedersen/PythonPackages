import os
import re
import requests
from urllib.parse import quote
from .config import VAULT_PATH

# Create PDF directory inside your Obsidian vault
PDF_DIR = os.path.join(VAULT_PATH, "Papers")
os.makedirs(PDF_DIR, exist_ok=True)


# -----------------------------
# Utility: sanitize filenames
# -----------------------------
def sanitize_title(title: str) -> str:
    title = title.lower()
    title = re.sub(r"[^a-z0-9]+", "_", title)
    return title.strip("_")


# -----------------------------
# Extract PDF candidates from OpenAlex
# -----------------------------
def extract_pdf_candidates(paper):
    urls = []

    # 1. OpenAlex best OA location
    loc = paper.get("best_oa_location")
    if loc and loc.get("url"):
        urls.append(loc["url"])

    # 2. arXiv
    arxiv_id = paper.get("ids", {}).get("arxiv")
    if arxiv_id:
        urls.append(f"https://arxiv.org/pdf/{arxiv_id}.pdf")

    # 3. DOI → direct DOI link
    doi = paper.get("doi")
    if doi:
        urls.append(f"https://doi.org/{doi}")

    return urls


# -----------------------------
# Unpaywall lookup
# -----------------------------
def query_unpaywall(doi, email="your_email@example.com"):
    if not doi:
        return None

    url = f"https://api.unpaywall.org/v2/{doi}?email={email}"
    try:
        r = requests.get(url, timeout=10)
        if r.status_code != 200:
            return None

        data = r.json()
        oa = data.get("best_oa_location")
        if oa and oa.get("url_for_pdf"):
            return oa["url_for_pdf"]
    except:
        pass

    return None


# -----------------------------
# Semantic Scholar lookup
# -----------------------------
def query_semantic_scholar(doi):
    if not doi:
        return None

    url = f"https://api.semanticscholar.org/graph/v1/paper/DOI:{doi}?fields=title,openAccessPdf"
    try:
        r = requests.get(url, timeout=10)
        if r.status_code != 200:
            return None

        data = r.json()
        pdf = data.get("openAccessPdf", {}).get("url")
        return pdf
    except:
        return None


# -----------------------------
# Download PDF
# -----------------------------
def download_pdf(url, save_path):
    try:
        r = requests.get(url, timeout=15)
        if (
            r.status_code == 200
            and "application/pdf" in r.headers.get("content-type", "")
        ):
            with open(save_path, "wb") as f:
                f.write(r.content)
            return True
    except:
        pass
    return False


# -----------------------------
# Main resolver
# -----------------------------
def resolve_pdf(paper):
    """
    Attempts to find and download a PDF for a given OpenAlex paper.
    Returns the local file path if successful, otherwise None.
    """

    title = paper.get("title", "paper")
    filename = sanitize_title(title) + ".pdf"
    save_path = os.path.join(PDF_DIR, filename)

    # Skip if already downloaded
    if os.path.exists(save_path):
        return save_path

    candidates = extract_pdf_candidates(paper)

    doi = paper.get("doi")
    if doi:
        # Try Unpaywall
        pdf = query_unpaywall(doi)
        if pdf:
            candidates.append(pdf)

        # Try Semantic Scholar
        pdf = query_semantic_scholar(doi)
        if pdf:
            candidates.append(pdf)

    # Deduplicate
    candidates = list(dict.fromkeys(candidates))

    # Try downloading each candidate
    for url in candidates:
        if download_pdf(url, save_path):
            return save_path

    return None
