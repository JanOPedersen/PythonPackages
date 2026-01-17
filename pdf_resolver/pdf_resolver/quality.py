# pdf_resolver/quality.py
import re

def compute_extraction_quality(text: str) -> float:
    if not text:
        return 0.0
    length = len(text)
    alpha = sum(c.isalpha() for c in text)
    alpha_ratio = alpha / max(length, 1)

    lines = text.splitlines()
    broken_lines = sum(1 for l in lines if l.endswith("-"))
    broken_ratio = broken_lines / max(len(lines), 1)

    has_abstract = bool(re.search(r"\babstract\b", text, re.IGNORECASE))
    has_intro = bool(re.search(r"\bintroduction\b", text, re.IGNORECASE))

    score = 0.4 * alpha_ratio + 0.2 * (1 - broken_ratio) + 0.2 * (1 if has_abstract else 0) + 0.2 * (1 if has_intro else 0)
    return max(0.0, min(1.0, score))
