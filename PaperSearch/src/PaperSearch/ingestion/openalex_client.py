import requests
from .utils import canonicalise_doi
import time
from typing import List, Dict, Optional
from tqdm import tqdm

OPENALEX_API_BASE_URL = "https://api.openalex.org/works"

class OpenAlexSearchClient:
    """
    A robust OpenAlex search helper with:
    - cursor-based pagination
    - retry logic
    - no magic numbers
    - target-size control (e.g., ~1000 records)
    """

    BASE_URL = "https://api.openalex.org/works"

    def __init__(
        self,
        per_page: int = 200,
        max_retries: int = 5,
        retry_backoff: float = 1.5,
        timeout: int = 30,
    ):
        """
        per_page: OpenAlex maximum is 200, but caller can override.
        max_retries: retry attempts for transient errors.
        retry_backoff: exponential backoff multiplier.
        timeout: HTTP timeout.
        """
        self.per_page = per_page
        self.max_retries = max_retries
        self.retry_backoff = retry_backoff
        self.timeout = timeout

    # ------------------------------------------------------------
    # Internal: perform a single request with retries
    # ------------------------------------------------------------
    def _request(self, params: Dict) -> Dict:
        for attempt in range(1, self.max_retries + 1):
            try:
                resp = requests.get(
                    self.BASE_URL,
                    params=params,
                    timeout=self.timeout,
                )
                resp.raise_for_status()
                return resp.json()

            except requests.HTTPError as e:
                # 400 usually means bad params, so don't retry
                if resp.status_code == 400:
                    raise ValueError(f"Bad request to OpenAlex: {resp.text}") from e

                # 429 or 500/503 → retry
                if resp.status_code in (429, 500, 502, 503, 504):
                    sleep_time = self.retry_backoff ** attempt
                    time.sleep(sleep_time)
                    continue

                raise

            except requests.RequestException:
                # network issues → retry
                sleep_time = self.retry_backoff ** attempt
                time.sleep(sleep_time)
                continue

        raise RuntimeError("OpenAlex request failed after retries")

    # ------------------------------------------------------------
    # Public: search with cursor pagination
    # ------------------------------------------------------------
    def search(
        self,
        query: str,
        select_fields: Optional[List[str]] = None,
        target_records: int = 1000,
    ) -> List[Dict]:
        """
        Perform a search and return up to target_records results.
        Uses cursor-based pagination.

        target_records: how many results you want (approx).
        """

        if select_fields is None:
            select_fields = [
                "id",
                "doi",
                "title",
                "publication_year",
                "authorships",
                "concepts",
                "cited_by_count",
                "referenced_works",
                "abstract_inverted_index",
                "primary_location",
                "best_oa_location",
            ]

        params = {
            "search": query,
            "per_page": self.per_page,
            "cursor": "*",
            "select": ",".join(select_fields),
        }

        results = []
        next_cursor = "*"

        with tqdm(desc=f"OpenAlex search: {query}", unit="record") as pbar:
            while next_cursor and len(results) < target_records:
                params["cursor"] = next_cursor
                data = self._request(params)

                batch = data.get("results", [])
                results.extend(batch)
                pbar.update(len(batch))

                next_cursor = data.get("meta", {}).get("next_cursor")

                # Stop early if OpenAlex has no more results
                if not batch:
                    break

        return results[:target_records]

def search_openalex_query(
    query: str,
    limit: int = 10,
    fields: list[str] | None = None,
    expand: list[str] | None = None,
):
    url = OPENALEX_API_BASE_URL
    
    params = {
        "search": query,
        "per-page": limit,
    }

    # Add metadata field selection
    if fields:
        params["select"] = ",".join(fields)

    # Add expansion of nested metadata
    if expand:
        params["expand"] = ",".join(expand)

    r = requests.get(url, params=params, timeout=10)
    r.raise_for_status()
    return r.json().get("results", [])

def openalex_search_query(query: str, limit: int = 10):
    results = search_openalex_query(query,
    fields=[
        "id", 
        "doi", 
        "title", 
        "publication_year", 
        "authorships", 
        "concepts", 
        "cited_by_count",
        "referenced_works",
        "abstract_inverted_index",
        "primary_location",
        "best_oa_location",
        ],
    limit=limit)
   
    for work in results:
            doi = work.get("doi")
            if doi:
                work["doi"] = canonicalise_doi(doi)

    return results

def openalex_search_query_paginated(query: str, limit: int = 10, per_page: int = 200) -> List[Dict]:
    client = OpenAlexSearchClient(per_page=per_page)
    results = client.search(query, target_records=limit)

    for w in results:
        if w.get("doi"):
            w["doi"] = canonicalise_doi(w["doi"])

    return results

def openalex_search_doi(doi: str) -> dict | None:
    url = f"{OPENALEX_API_BASE_URL}/works/https://doi.org/{doi}"
    resp = requests.get(url, timeout=10)

    if resp.status_code != 200:
        return None

    data = resp.json()

    return {
        "concepts": [c["display_name"] for c in data.get("concepts", [])],
        "cited_by_count": data.get("cited_by_count"),
        "referenced_works": data.get("referenced_works", []),
        "id": data.get("id"),
        "title": data.get("title"),
        "publication_year": data.get("publication_year"),
        "authorships": data.get("authorships", []),
        "doi": canonicalise_doi(data.get("doi")),
        "abstract_inverted_index": data.get("abstract_inverted_index"),
        "primary_location": data.get("primary_location"),
        "best_oa_location": data.get("best_oa_location"),
    }