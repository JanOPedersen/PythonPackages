import requests
import urllib.parse
from .utils import canonicalise_doi
import urllib.parse


# -----------------------------
# CONFIGURATION
# -----------------------------
ZOTERO_USER_ID = "19326399"
ZOTERO_API_KEY = "rPueCGyG42hsil3gQiqfutPe"
ZOTERO_API_ROOT = f"https://api.zotero.org/users/{ZOTERO_USER_ID}"
CROSSREF_BASE_URL = "https://api.crossref.org/works"

HEADERS = {
    "Zotero-API-Key": ZOTERO_API_KEY,
    "Content-Type": "application/json"
}


# -----------------------------
# CrossRef search
# -----------------------------
def search_crossref_query(
        query: str, 
        limit: int = 10,
        fields: list[str] | None = None,
    ):
    url = CROSSREF_BASE_URL
    params = {"query": query, "rows": limit}

    r = requests.get(url, params=params, timeout=10)
    r.raise_for_status()

    items = r.json()["message"]["items"]

    # If no field filtering requested, return full items
    if not fields:
        return items

    # Otherwise return only the selected subset
    filtered = []
    for item in items:
        filtered.append({f: item.get(f) for f in fields})

    return filtered

def _search_crossref_query_paginated(query: str,
                                     fields: list[str],
                                     limit: int,
                                     rows_per_page: int = 200):
    """
    Paginated Crossref search that mimics the behaviour of search_crossref_query,
    but fetches results in multiple pages to avoid 400 errors.
    """
    url = "https://api.crossref.org/works"
    collected = []
    offset = 0

    while len(collected) < limit:
        rows = min(rows_per_page, limit - len(collected))

        params = {
            "query": query,
            "rows": rows,
            "offset": offset
        }

        r = requests.get(url, params=params, timeout=10)
        r.raise_for_status()

        items = r.json()["message"]["items"]
        if not items:
            break

        # If fields filtering is desired, apply it here
        if fields:
            filtered = []
            for item in items:
                filtered.append({k: item.get(k) for k in fields})
            items = filtered

        collected.extend(items)

        # Stop early if Crossref returned fewer than requested
        if len(items) < rows:
            break

        offset += rows

    return collected

def crossref_search_query(query: str, limit: int = 10):
    """
    Public API: identical structure to your original function,
    but internally uses pagination to avoid Crossref 400 errors.
    """
    results = _search_crossref_query_paginated(
        query=query,
        fields=["title", "DOI", "author", "published",
                "is-referenced-by-count", "reference"],
        limit=limit
    )

    # Canonicalise DOIs exactly as before
    for work in results:
        doi = work.get("DOI")
        if doi:
            work["DOI"] = canonicalise_doi(doi)

    return results

def crossref_search_doi(doi: str) -> dict | None:
    url = f"{CROSSREF_BASE_URL}/works/{doi}"
    resp = requests.get(url, timeout=10)

    if resp.status_code != 200:
        return None

    data = resp.json().get("message", {})

    return {
        "title": data.get("title", [None])[0],
        "author": [
            {
                "name": f"{a.get('given', '')} {a.get('family', '')}".strip(),
                "orcid": a.get("ORCID"),
                "affiliation": a.get("affiliation", [])
            }
            for a in data.get("author", [])
        ],
        "year": data.get("issued", {}).get("date-parts", [[None]])[0][0],
        "references_count": data.get("references-count"),
        "is_referenced_by_count": data.get("is-referenced-by-count"),
        "DOI": canonicalise_doi(data.get("DOI")),
        "URL": data.get("URL"),
        "reference": data.get("reference", []),
    }

'''
def crossref_lookup(title: str):
    """
    Query Crossref using only a paper title.
    Returns a dictionary with metadata if found, otherwise None.
    """

    # Encode title for URL
    query = urllib.parse.quote(title)

    # Crossref API endpoint
    url = f"https://api.crossref.org/works?query.title={query}&rows=5"

    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
    except Exception as e:
        print(f"Request error: {e}")
        return None

    data = response.json()

    # No results
    if "message" not in data or "items" not in data["message"]:
        return None

    items = data["message"]["items"]
    if not items:
        return None

    # Pick the best match (first item is usually the highest score)
    item = items[0]

    # Extract metadata safely
    metadata = {
        "title": item.get("title", [""])[0],
        "DOI": item.get("DOI"),
        "type": item.get("type"),
        "publisher": item.get("publisher"),
        "URL": item.get("URL"),
        "published_year": (
            item.get("issued", {})
                .get("date-parts", [[None]])[0][0]
        ),
        "authors": [
            f"{a.get('given', '')} {a.get('family', '')}".strip()
            for a in item.get("author", [])
        ] if "author" in item else [],
        "container_title": item.get("container-title", [""])[0],
        "volume": item.get("volume"),
        "issue": item.get("issue"),
        "page": item.get("page"),
        "score": item.get("score"),  # Crossref relevance score
    }

    return metadata
'''

# -----------------------------
# CROSSREF LOOKUP
# -----------------------------
def crossref_lookup(title: str):
    query = urllib.parse.quote(title)
    url = f"https://api.crossref.org/works?query.title={query}&rows=5"

    try:
        r = requests.get(url, timeout=10)
        r.raise_for_status()
    except Exception:
        return None

    items = r.json().get("message", {}).get("items", [])
    if not items:
        return None

    item = items[0]

    return {
        "DOI": item.get("DOI"),
        "container_title": item.get("container-title", [""])[0],
        "published_year": (
            item.get("issued", {}).get("date-parts", [[None]])[0][0]
        ),
        "volume": item.get("volume"),
        "issue": item.get("issue"),
        "page": item.get("page"),
    }

# -----------------------------
# ZOTERO API HELPERS
# -----------------------------
def get_all_items_key(collection_key, max_items=1000):
    """
    Fetch all bibliographic items from a specific Zotero collection
    using pagination. Stops after max_items for debugging.
    """
    items = []

    url = f"{ZOTERO_API_ROOT}/collections/{collection_key}/items?limit=100"

    while url:
        r = requests.get(url, headers=HEADERS)
        r.raise_for_status()

        batch = r.json()
        items.extend(batch)

        # Debug cap: stop after max_items
        if len(items) >= max_items:
            items = items[:max_items]
            break

        # Parse pagination links
        link_header = r.headers.get("Link", "")
        next_url = None

        if link_header:
            for part in link_header.split(","):
                section = part.split(";")
                if len(section) == 2:
                    link = section[0].strip()[1:-1]  # remove < >
                    rel = section[1].strip()
                    if rel == 'rel="next"':
                        next_url = link

        url = next_url

    # Filter to bibliographic items only
    biblio_types = {
        "journalArticle", "conferencePaper", "bookSection",
        "report", "Report", "thesis", "preprint", "manuscript"
    }

    filtered = [
        item for item in items
        if item["data"].get("itemType") in biblio_types
    ]

    return filtered



def get_all_items(max_items=1000):
    """
    Fetch all bibliographic items from Zotero using pagination.
    Stops after max_items for debugging.
    """
    items = []
    url = f"{ZOTERO_API_ROOT}/items?limit=100"

    while url:
        r = requests.get(url, headers=HEADERS)
        r.raise_for_status()

        batch = r.json()
        items.extend(batch)

        # Debug cap: stop after max_items
        if len(items) >= max_items:
            items = items[:max_items]
            break

        # Parse pagination links
        link_header = r.headers.get("Link", "")
        next_url = None

        if link_header:
            for part in link_header.split(","):
                section = part.split(";")
                if len(section) == 2:
                    link = section[0].strip()[1:-1]  # remove < >
                    rel = section[1].strip()
                    if rel == 'rel="next"':
                        next_url = link

        url = next_url  # continue or stop

    # Filter to bibliographic items only
    biblio_types = {
        "journalArticle", "conferencePaper", "bookSection","Report",
        "report", "thesis", "preprint", "manuscript"
    }

    filtered = [
        item for item in items
        if item["data"].get("itemType") in biblio_types
    ]

    return filtered


def update_zotero_item(item, metadata):
    key = item["key"]
    version = item["version"]
    data = item["data"]
    item_type = data.get("itemType")

    # DOI is valid for all bibliographic types
    if metadata.get("DOI") and not data.get("DOI"):
        data["DOI"] = metadata["DOI"]

    # Handle container title based on item type
    ct = metadata.get("container_title")
    if ct:
        if item_type == "journalArticle" and not data.get("publicationTitle"):
            data["publicationTitle"] = ct

        elif item_type == "conferencePaper" and not data.get("proceedingsTitle"):
            data["proceedingsTitle"] = ct

        elif item_type == "bookSection" and not data.get("bookTitle"):
            data["bookTitle"] = ct

        # Books do NOT accept container titles → skip

    # Year
    if metadata.get("published_year") and not data.get("date"):
        data["date"] = str(metadata["published_year"])

    # Volume, issue, pages (valid for journal articles & conference papers)
    if item_type in ("journalArticle", "conferencePaper"):
        if metadata.get("volume") and not data.get("volume"):
            data["volume"] = metadata["volume"]

        if metadata.get("issue") and not data.get("issue"):
            data["issue"] = metadata["issue"]

        if metadata.get("page") and not data.get("pages"):
            data["pages"] = metadata["page"]

    # Prepare payload
    payload = {
        "key": key,
        "version": version,
        "data": data
    }

    url = f"{ZOTERO_API_ROOT}/items/{key}"

    headers = {
        "Zotero-API-Key": ZOTERO_API_KEY,
        "Content-Type": "application/json",
        "If-Unmodified-Since-Version": str(version)
    }

    r = requests.put(url, headers=headers, json=payload)
    return r.status_code in (200, 204)


def lookup_and_save_metadata(collection_key):
    """
    Given a Zotero collection key, look up missing metadata
    for items in that collection using Crossref, and update Zotero.
    """
    items = get_all_items_key(collection_key, max_items=1000000)
    print(f"Found {len(items)} Zotero items")

    for item in tqdm(items, desc="Looking up metadata"):
        data = item["data"]
        title = data.get("title")
        doi = data.get("DOI")

        if not title:
            continue

        if doi:
            continue  # already has DOI

        metadata = crossref_lookup(title)
        if not metadata:
            continue

        print(f"Found metadata for title: {title}")
        update_zotero_item(item, metadata)
        time.sleep(1)  # be polite to Crossref