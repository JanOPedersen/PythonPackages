import json
import re
from typing import Dict, Any, List

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

def yaml_list(items: List[str]) -> str:
    """Convert a Python list of strings into a YAML list."""
    if not items:
        return "[]"
    return "\n".join([f"  - {item}" for item in items])


def sanitize_title(title: str) -> str:
    """Sanitize title for safe Obsidian filenames."""
    return re.sub(r'[\\/*?:"<>|]', "", title).strip()


def create_markdown(paper: Dict[str, Any], summary: Dict[str, Any]) -> str:
    """
    Create Obsidian-friendly Markdown with valid YAML front matter.
    `paper` is the OpenAlex metadata.
    `summary` is the structured dict from summarize_paper().
    """

    title = paper.get("title", "Untitled")
    authors = paper.get("authorships", [])
    year = paper.get("publication_year", "")
    venue = paper.get("host_venue", {}).get("display_name", "")

    # Extract author names
    author_names = [a["author"]["display_name"] for a in authors if "author" in a]

    # YAML front matter
    front_matter = f"""---
title: "{title}"
authors:
{yaml_list(author_names)}
year: {year}
venue: "{venue}"
---
"""

    # Helper to conditionally add sections
    def section(header: str, content: Any) -> str:
        if not content:
            return ""
        if isinstance(content, list):
            if not content:
                return ""
            content = "\n".join([f"- {item}" for item in content])
        return f"## {header}\n{content}\n\n"

    md = front_matter

    md += section("Summary", summary.get("summary"))
    md += section("Key Contributions", summary.get("contributions"))
    md += section("Limitations", summary.get("limitations"))
    md += section("Future Work", summary.get("future_work"))

    return md.strip()
