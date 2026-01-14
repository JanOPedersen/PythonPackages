import requests
from urllib.parse import quote
from .config import OPENALEX_BASE, RL_CONCEPT_ID, MAX_RESULTS
import ollama
import re

def expand_query(user_query: str, llm_model: str):
    """
    Expand a natural-language query into short OpenAlex-friendly keywords.
    The LLM output is sanitized so OR-chains, parentheses, and long phrases
    are automatically removed.
    """

    prompt = f"""
    Produce a list of short search keywords (1–3 words each)
    related to this query:

    "{user_query}"

    RULES:
    - Return ONLY a comma-separated list
    - No 'OR'
    - No parentheses
    - No long phrases
    - No sentences
    - No boolean logic
    - No explanations
    """

    response = ollama.chat(
        model=llm_model,
        messages=[{"role": "user", "content": prompt}]
    )

    raw = response["message"]["content"].strip()

    # --- SANITIZATION LAYER ---
    # Remove OR, parentheses, periods
    cleaned = re.sub(r"\bOR\b", ",", raw, flags=re.IGNORECASE)
    cleaned = cleaned.replace("(", "").replace(")", "")
    cleaned = cleaned.replace(".", "")

    # Split on commas
    terms = [t.strip() for t in cleaned.split(",") if t.strip()]

    # Remove long phrases (>3 words)
    terms = [t for t in terms if len(t.split()) <= 3]

    # Deduplicate
    terms = list(dict.fromkeys(terms))

    return terms

def fetch_papers(terms):
    """
    Multi-term OpenAlex search.
    `terms` must be a list of strings.
    Returns a deduplicated list of papers.
    """

    all_results = []

    for term in terms:
        term = term.strip()
        if not term:
            continue

        url = (
            f"{OPENALEX_BASE}"
            f"?search={quote(term)}"
            f"&filter=concepts.id:{RL_CONCEPT_ID}"
            f"&per-page={MAX_RESULTS}"
        )

        print("Querying:", url)  # helpful debug line

        response = requests.get(url)
        response.raise_for_status()

        results = response.json().get("results", [])
        all_results.extend(results)

    # Deduplicate by OpenAlex ID
    unique = {p["id"]: p for p in all_results}
    return list(unique.values())

