import json
import ollama
from typing import Dict, Any, Optional


def safe_json_loads(text: str) -> Optional[Dict[str, Any]]:
    """Attempt to parse JSON safely, returning None on failure."""
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return None


def summarize_paper(title: str, abstract: str) -> Dict[str, Any]:
    """
    Robust summarizer that:
    - requests structured JSON
    - retries if output is empty
    - repairs malformed JSON
    - falls back to non-JSON mode
    - guarantees a dict return
    """

    # --- 1. Build the prompt ---
    base_prompt = f"""
    You are a research assistant. Summarize the following paper in structured JSON.

    Title: {title}

    Abstract:
    {abstract}

    Return ONLY valid JSON with the following fields:
    - "summary"
    - "contributions"
    - "limitations"
    - "future_work"
    """

    # --- 2. First attempt: strict JSON mode ---
    response = ollama.chat(
        model="mistral",
        messages=[{"role": "user", "content": base_prompt}],
        options={"format": "json"}
    )

    raw = response.get("message", {}).get("content", "").strip()

    # Empty output → retry once
    if not raw:
        # Optional: log this
        print("[WARN] Empty response in strict JSON mode. Retrying...")

        response = ollama.chat(
            model="mistral",
            messages=[{"role": "user", "content": base_prompt}],
            options={"format": "json"}
        )
        raw = response.get("message", {}).get("content", "").strip()

    # Try parsing
    parsed = safe_json_loads(raw)

    # --- 3. If strict JSON failed, attempt repair ---
    if parsed is None:
        print("[WARN] Strict JSON mode returned invalid JSON. Attempting repair...")

        repair_prompt = f"""
        The following text should be valid JSON but is malformed:

        {raw}

        Repair it and return ONLY valid JSON.
        """

        repair = ollama.chat(
            model="mistral",
            messages=[{"role": "user", "content": repair_prompt}],
            options={"format": "json"}
        )

        repaired_raw = repair.get("message", {}).get("content", "").strip()
        parsed = safe_json_loads(repaired_raw)

    # --- 4. If still broken, fallback to non-JSON summarization ---
    if parsed is None:
        print("[WARN] JSON repair failed. Falling back to plain text summarization.")

        fallback = ollama.chat(
            model="mistral",
            messages=[{"role": "user", "content": base_prompt}],
        )

        text = fallback.get("message", {}).get("content", "").strip()

        # Return a minimal but valid structure
        return {
            "summary": text,
            "contributions": [],
            "limitations": [],
            "future_work": []
        }

    # --- 5. Guarantee a dict with all expected fields ---
    return {
        "summary": parsed.get("summary", ""),
        "contributions": parsed.get("contributions", []),
        "limitations": parsed.get("limitations", []),
        "future_work": parsed.get("future_work", [])
    }
