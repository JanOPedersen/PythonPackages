import json
import re

def safe_json_loads(text):
    """
    Extract the first valid JSON object from a string using brace counting.
    Works even if the model adds text before or after the JSON.
    """

    start = text.find("{")
    if start == -1:
        raise ValueError("No JSON object found in model output")

    brace_count = 0
    in_json = False

    for i, ch in enumerate(text[start:], start=start):
        if ch == "{":
            brace_count += 1
            in_json = True
        elif ch == "}":
            brace_count -= 1

        if in_json and brace_count == 0:
            json_str = text[start:i+1]
            break
    else:
        raise ValueError("JSON braces never balanced")

    # Try parsing the extracted JSON
    try:
        return json.loads(json_str)
    except json.JSONDecodeError:
        # Attempt minimal cleanup
        cleaned = json_str.replace("\n", " ").replace("\t", " ")
        cleaned = cleaned.replace(", }", "}")
        cleaned = cleaned.replace(", }", "}")
        return json.loads(cleaned)


def create_markdown(paper, summary):
    # summary is already a dict
    md = f"""---
    title: "{paper.get('title', '')}"
    authors: {[a['author']['display_name'] for a in paper.get('authorships', [])]}
    year: {paper.get('publication_year', '')}
    venue: "{paper.get('host_venue', {}).get('display_name', '')}"
    ---

    ## Problem
    {summary.get('problem', '')}

    ## Method
    {summary.get('method', '')}

    ## Key Contributions
    {summary.get('key_contributions', '')}

    ## Architecture
    {summary.get('architecture', '')}

    ## Experiments
    {summary.get('experiments', '')}

    ## Limitations
    {summary.get('limitations', '')}

    ## Future Work
    {summary.get('future_work', '')}

    ## Relevance Score
    {summary.get('relevance_score', '')}
    """
    return md

