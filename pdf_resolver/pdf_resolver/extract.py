# pdf_resolver/extract.py
from typing import Optional

def extract_with_pymupdf(path: str) -> str:
    import fitz  # PyMuPDF
    text_parts = []
    with fitz.open(path) as doc:
        for page in doc:
            text_parts.append(page.get_text())
    return "\n".join(text_parts)

def extract_with_pdfminer(path: str) -> str:
    from io import StringIO
    from pdfminer.high_level import extract_text_to_fp
    output = StringIO()
    with open(path, "rb") as f:
        extract_text_to_fp(f, output)
    return output.getvalue()

def extract_text_from_pdf(path: str) -> Optional[str]:
    try:
        return extract_with_pymupdf(path)
    except Exception:
        try:
            return extract_with_pdfminer(path)
        except Exception:
            return None
