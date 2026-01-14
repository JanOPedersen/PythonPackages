# pdf_resolver/resolve.py
from typing import Optional, Any
from .types import PDFResolutionResult
from .download import download_pdf
from .extract import extract_text_from_pdf
from .quality import compute_extraction_quality

def get_field(obj, name, default=None):
    if hasattr(obj, name):
        return getattr(obj, name)
    if isinstance(obj, dict):
        return obj.get(name, default)
    return default

def _pick_pdf_url_from_openalex(meta: dict[str, Any]) -> Optional[str]:
    primary = meta.get("primary_location") or {}
    if primary.get("pdf_url"):
        return primary["pdf_url"]
    for loc in meta.get("locations", []):
        if loc.get("pdf_url"):
            return loc["pdf_url"]
    return None

def resolve_pdf_for_paper(
    paper: Any,
    *,
    openalex_meta: Optional[dict[str, Any]] = None,
    pdf_cache_dir: str = "data/pdfs",
    logger=None,
) -> PDFResolutionResult:
    paper_id = get_field(paper, "paper_id")
    title = get_field(paper, "title", "paper")
    explicit_pdf_url = get_field(paper, "pdf_url")

    strategy = None
    pdf_url = None
    local_path = None
    extracted_text = None
    quality = None
    error = None

    try:
        if explicit_pdf_url:
            pdf_url = explicit_pdf_url
            strategy = "explicit_pdf_url"
        elif openalex_meta:
            pdf_url = _pick_pdf_url_from_openalex(openalex_meta)
            strategy = "openalex_primary_location" if pdf_url else None

        if not pdf_url:
            strategy = None
            return PDFResolutionResult(
                paper_id=paper_id,
                pdf_url=None,
                local_path=None,
                extracted_text=None,
                strategy=None,
                quality_score=None,
                error="no_pdf_url_found",
            )

        local_path = download_pdf(pdf_url, pdf_cache_dir, f"{paper_id}")
        if not local_path:
            return PDFResolutionResult(
                paper_id=paper_id,
                pdf_url=pdf_url,
                local_path=None,
                extracted_text=None,
                strategy=strategy,
                quality_score=None,
                error="download_failed",
            )

        extracted_text = extract_text_from_pdf(local_path)
        if not extracted_text:
            return PDFResolutionResult(
                paper_id=paper_id,
                pdf_url=pdf_url,
                local_path=local_path,
                extracted_text=None,
                strategy=strategy,
                quality_score=None,
                error="extraction_failed",
            )

        quality = compute_extraction_quality(extracted_text)

        return PDFResolutionResult(
            paper_id=paper_id,
            pdf_url=pdf_url,
            local_path=local_path,
            extracted_text=extracted_text,
            strategy=strategy,
            quality_score=quality,
            error=None,
        )
    except Exception as e:
        if logger:
            logger.exception("PDF resolution failed for %s", paper_id)
        return PDFResolutionResult(
            paper_id=paper_id,
            pdf_url=pdf_url,
            local_path=local_path,
            extracted_text=extracted_text,
            strategy=strategy,
            quality_score=quality,
            error=str(e),
        )
