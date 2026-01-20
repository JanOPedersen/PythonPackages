# ingestion/pdf_utils.py
from pathlib import Path
from typing import Optional
from ingestion.models import Paper


def find_pdf_for_paper(paper: Paper, pdf_root: Path) -> Optional[Path]:
    """
    Very naive: look for files containing the paper_id or a slug of the title.
    You’ll likely replace this with a Zotero-attachment-aware resolver.
    """
    slug = "".join(c.lower() for c in paper.title if c.isalnum() or c in (" ", "-"))[:80]
    for pdf in pdf_root.rglob("*.pdf"):
        if paper.paper_id in pdf.name or slug in pdf.name.lower():
            return pdf
    return None


def extract_text_from_pdf(pdf_path: Path) -> str:
    # Placeholder: integrate real PDF extraction here
    # e.g. with pymupdf or pdfminer.six
    return f"FULL TEXT FROM {pdf_path.name} (stub)"


def attach_pdf_and_text(paper: Paper, pdf_root: Path) -> Paper:
    pdf = find_pdf_for_paper(paper, pdf_root)
    if pdf:
        paper.pdf_path = str(pdf)
        paper.full_text = extract_text_from_pdf(pdf)
    return paper
