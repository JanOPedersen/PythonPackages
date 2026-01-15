# zotero_classify

Convert Zotero-style hierarchical JSON into compact Dewey-like Markdown tables.

## Install

pip install .


## Usage

zotero-classify hierarchy.json  hierarchy.md


## Import in Python

```python
from zotero_classify import parse_json_to_markdown
parse_json_to_markdown("hierarchy.json", "hierarchy.md")
