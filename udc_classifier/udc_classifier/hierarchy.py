import json
import os
import re


def clean_path(p):
    if not p:
        return None
    if isinstance(p, str) and p.startswith("attachments:"):
        return p.replace("attachments:", "", 1)
    return p


def extract_code_from_name(name):
    if not isinstance(name, str):
        return None
    m = re.match(r"^\s*(\d+)", name)
    return m.group(1) if m else None


def walk_hierarchy(tree, root_dir):
    codes_dict = {}

    def walk(node, prefix):
        name = node.get("name")
        part = extract_code_from_name(name)
        new_prefix = prefix + [part] if part else prefix

        for item in node.get("items", []):
            for att in item.get("attachments", []):
                raw_path = att.get("path")
                cleaned = clean_path(raw_path)
                if cleaned:
                    full = os.path.normpath(os.path.join(root_dir, cleaned))
                    if new_prefix:
                        codes_dict[full] = ".".join(new_prefix)

        for child in node.get("children", []):
            walk(child, new_prefix)

    walk(tree[0], [])
    return codes_dict
