import json
from pathlib import Path


def parse_name(name: str):
    parts = name.split(" ", 1)
    if len(parts) == 1:
        return parts[0], ""
    return parts[0], parts[1]


def build_code(parent_code: str | None, num: str) -> str:
    if parent_code is None:
        return num

    if parent_code.isdigit():
        length = len(parent_code)

        if length == 1:
            if len(num) == 2:
                return num.zfill(3)
            return parent_code + num

        if length == 2:
            return parent_code + num

        if length == 3:
            return f"{parent_code}.{num}"

    parts = parent_code.split(".")
    parts.append(num)
    return ".".join(parts)


def compact_code(code: str) -> str:
    # Temporary hack: strip leading 'books' if present
    if code.startswith("books"):
        code = code[len("books"):]

    raw = code.replace(".", "")

    if not raw.isdigit():
        return code

    if len(raw) <= 3:
        return raw

    root = raw[:3]
    tail = raw[3:]

    groups = [tail[i:i+3] for i in range(0, len(tail), 3)]
    return ".".join([root] + groups)


def walk(node, parent_code=None, results=None):
    if results is None:
        results = []

    name = node.get("name", "")
    if name and name != "papers":
        num, desc = parse_name(name)
        code = build_code(parent_code, num)
        code = compact_code(code)
        results.append((code, desc))
        parent_code = code

    for child in node.get("children", []):
        walk(child, parent_code, results)

    return results


def generate_markdown_table(rows):
    lines = [
        "| Code | Description |",
        "|------|-------------|"
    ]
    for code, desc in rows:
        lines.append(f"| {code} | {desc} |")
    return "\n".join(lines)


def parse_json_to_markdown(json_path: str, md_path: str):
    raw = json.loads(Path(json_path).read_text())

    if isinstance(raw, list):
        rows = []
        for node in raw:
            rows.extend(walk(node))
    else:
        rows = walk(raw)

    md = generate_markdown_table(rows)
    Path(md_path).write_text(md, encoding="utf-8")
    return md_path
