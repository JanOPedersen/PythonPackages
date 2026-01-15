import argparse
from .parser import parse_json_to_markdown


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Convert Zotero hierarchy JSON into a Markdown classification table."
    )
    parser.add_argument("json_path", help="Input JSON file")
    parser.add_argument("md_path", help="Output Markdown file")

    args = parser.parse_args(argv)
    parse_json_to_markdown(args.json_path, args.md_path)

    print(f"Markdown written to {args.md_path}")
