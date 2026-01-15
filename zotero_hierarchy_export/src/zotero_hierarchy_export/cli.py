from pathlib import Path
from .extractor import export_hierarchy, export_to_json

def main():
    print("CLI started")
    import argparse

    parser = argparse.ArgumentParser(description="Export Zotero hierarchy to JSON")
    parser.add_argument(
        "--db",
        type=Path,
        required=True,
        help="Path to zotero.sqlite"
    )
    parser.add_argument(
        "--out",
        type=Path,
        required=True,
        help="Output JSON file"
    )

    args = parser.parse_args()

    hierarchy = export_hierarchy(args.db)
    export_to_json(hierarchy, args.out)

    print(f"Exported hierarchy to {args.out}")
