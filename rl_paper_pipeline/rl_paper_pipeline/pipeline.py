from .openalex_search import fetch_papers, expand_query
from .summarizer import summarize_paper
from .markdown_generator import create_markdown
from .save import save_markdown
from .start_ollama import ensure_ollama_running
from .config import LLM_MODEL

def decode_abstract(inv_index):
    if not inv_index:
        return None
    # OpenAlex stores abstracts as a word-position map
    words = sorted([(pos, word) for word, positions in inv_index.items() for pos in positions])
    return " ".join(word for pos, word in words)

def run_pipeline():
    print("Starting pipeline...")
    print("Starting Ollama server...")
    ensure_ollama_running()
    print("Ollama server is ready.")

    expanded_terms = expand_query("use of grid worlds in reinforcement learning", LLM_MODEL)
    print("Expanded terms:", expanded_terms)
    papers = fetch_papers(expanded_terms)

    print(f"Found {len(papers)} papers")

    i = 0
    for p in papers:
        i += 1
        if i > 3:
            break

        title = p.get("title", "")
        abstract = decode_abstract(p.get("abstract_inverted_index"))
        print("Title:", title)
        if not abstract:
            print("No abstract available, skipping...")
            continue

        summary = summarize_paper(title, abstract)
        md = create_markdown(p, summary)
        filename = f"{title}.md"
        save_markdown(md, filename)

    print("Pipeline complete.")
