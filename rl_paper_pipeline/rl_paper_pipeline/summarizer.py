import ollama

def summarize_paper_old(title, abstract):
    prompt = f"""
    Return ONLY valid JSON. No commentary. No markdown. No backticks.

    Use EXACTLY this structure:

    {{
    "problem": "",
    "method": "",
    "key_contributions": "",
    "architecture": "",
    "experiments": "",
    "limitations": "",
    "future_work": "",
    "relevance_score": 0.0
    }}

    Fill in the values based on the paper below.

    Title: {title}
    Abstract: {abstract}
    """

    response = ollama.chat(
        model="mistral",
        messages=[{"role": "user", "content": prompt}],
        options={"format": "json"}
    )

    return response["message"]["content"]


import json
import ollama

def summarize_paper(title, abstract):
    system_prompt = """
    You are a JSON-only model. 
    You MUST return a single valid JSON object.
    No commentary. No markdown. No backticks. No text before or after the JSON.
    No trailing commas. No unescaped quotes.
    """

    user_prompt = f"""
    Use EXACTLY this structure:

    {{
    "problem": "",
    "method": "",
    "key_contributions": "",
    "architecture": "",
    "experiments": "",
    "limitations": "",
    "future_work": "",
    "relevance_score": 0.0
    }}

    Fill in the values based on the paper below.

    Title: {title}
    Abstract: {abstract}
    """

    # First attempt
    response = ollama.chat(
        model="mistral",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        options={"format": "json"}
    )

    raw = response["message"]["content"].strip()

    # Try parsing directly
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        pass  # fall through to repair step

    # If the model produced malformed JSON, repair it
    repair_prompt = f"""
    Fix the following JSON so that it is valid and strictly parseable.
    Return ONLY the corrected JSON object.

    {raw}
    """

    repair = ollama.chat(
        model="mistral",
        messages=[{"role": "user", "content": repair_prompt}],
        options={"format": "json"}
    )

    repaired_raw = repair["message"]["content"].strip()

    return json.loads(repaired_raw)

