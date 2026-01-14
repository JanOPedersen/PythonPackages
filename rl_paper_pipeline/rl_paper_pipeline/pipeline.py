from .openalex_search import search_openalex_rl
from .summarizer import summarize_paper
from .markdown_generator import create_markdown
from .save import save_markdown
from .start_ollama import ensure_ollama_running

def decode_abstract(inv_index):
    if not inv_index:
        return None
    # OpenAlex stores abstracts as a word-position map
    words = sorted([(pos, word) for word, positions in inv_index.items() for pos in positions])
    return " ".join(word for pos, word in words)


def run_pipeline():
    print("Starting pipeline...")
    papers = search_openalex_rl()
    print(f"Found {len(papers)} papers")

    print("Starting Ollama server...")
    ensure_ollama_running()
    print("Ollama server is ready.")

    for p in papers:
        title = p.get("title", "")
        abstract = decode_abstract(p.get("abstract_inverted_index"))

        print("Title:", title)
        print("Has abstract:", bool(abstract))

        if not abstract:
            continue

        summary = summarize_paper(title, abstract)
        md = create_markdown(p, summary)
        filename = f"{title}.md"
        save_markdown(md, filename)

    print("Pipeline complete.")
