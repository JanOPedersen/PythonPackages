from pathlib import Path
from .extractor import export_hierarchy, export_to_json

def main(argv=None):
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

    parser.add_argument(
        "--root-key",
        type=str,
        required=False,
        help="Root collection key to filter hierarchy"
    )

    args = parser.parse_args(argv)

    hierarchy = export_hierarchy(args.db, root_key=args.root_key)
    export_to_json(hierarchy, args.out)

    print(f"Exported hierarchy to {args.out}")
