import re
import os
from .config import VAULT_PATH

def sanitize_filename(name):
    # Remove illegal Windows characters
    name = re.sub(r'[<>:"/\\|?*]', '', name)
    # Replace spaces with underscores
    name = name.replace(" ", "_")
    # Optional: shorten extremely long filenames
    return name[:150]

def save_markdown(content, filename):
    safe_name = sanitize_filename(filename)
    path = os.path.join(VAULT_PATH, safe_name)

    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
