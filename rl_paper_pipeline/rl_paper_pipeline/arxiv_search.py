import feedparser

def search_arxiv(query, max_results=20):
    url = f"http://export.arxiv.org/api/query?search_query=all:{query}&max_results={max_results}"
    feed = feedparser.parse(url)
    return feed.entries
