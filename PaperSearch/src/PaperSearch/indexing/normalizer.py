 # normalizer.py

import re
from .synonym_map import SYNONYMS

def normalize_text(text: str) -> str:
    text = text.lower()

    for canonical, variants in SYNONYMS.items():
        for v in variants:
            pattern = r"\b" + re.escape(v.lower()) + r"\b"
            text = re.sub(pattern, canonical, text)

    return text
