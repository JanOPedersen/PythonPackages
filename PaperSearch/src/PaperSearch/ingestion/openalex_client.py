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
                if resp.status_code == 400:
                    raise ValueError(f"Bad request to OpenAlex: {resp.text}") from e

                if resp.status_code in (429, 500, 502, 503, 504):
                    sleep_time = self.retry_backoff ** attempt
                    time.sleep(sleep_time)
                    continue

                raise

            except requests.RequestException:
                sleep_time = self.retry_backoff ** attempt
                time.sleep(sleep_time)
                continue

        raise RuntimeError("OpenAlex request failed after retries")

    # ------------------------------------------------------------
    # Public: search with cursor pagination + topic filters
    # ------------------------------------------------------------
    def search(
        self,
        query: str,
        select_fields: Optional[List[str]] = None,
        target_records: int = 1000,
        topics: Optional[List[str]] = None,
        year: int | None = None, 
    ) -> List[Dict]:
        """
        Perform a search and return up to target_records results.
        Uses cursor-based pagination.

        topics: list of concept names or concept IDs.
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

        # --------------------------------------------------------
        # Topic filtering
        # --------------------------------------------------------        
        if topics:
            filters = []
            for t in topics:
                if t.startswith("https://openalex.org/C"):
                    # Concept ID
                    filters.append(f"concepts.id:{t}")
                else:
                    raise ValueError(
                        f"Topic '{t}' must be an OpenAlex concept ID. "
                        "Filtering by display name is not supported by OpenAlex."
                    )
                
            # Add date filters here
            if year is not None:
                filters.append(f"from_publication_date:{year}-01-01")
                filters.append(f"to_publication_date:{year}-12-31")

            filters.append("has_abstract:true")
            #filters.append("primary_topic.domain:Computer Science")

            params["filter"] = ",".join(filters)
            params["sort"] = "cited_by_count:desc"

        # --------------------------------------------------------
        # Pagination loop
        # --------------------------------------------------------
        results = []
        next_cursor = "*"

        with tqdm(desc=f"OpenAlex search", unit="record") as pbar:
            while next_cursor and len(results) < target_records:
                params["cursor"] = next_cursor
                data = self._request(params)

                batch = data.get("results", [])
                results.extend(batch)
                pbar.update(len(batch))

                next_cursor = data.get("meta", {}).get("next_cursor")

                if not batch:
                    break

        return results[:target_records]

def openalex_search_query(
        query: str, 
        limit: int = 10, 
        per_page: int = 200,
        topics: list[str] | None = [
            "https://openalex.org/C119857082", #Machine Learning
            #"https://openalex.org/C41008148",  #Computer Science
            "https://openalex.org/C154945302",], #Artificial Intelligence
        year_range: tuple[int, int] | None = None,    
    ) -> List[Dict]:
    client = OpenAlexSearchClient(per_page=per_page)
    results = []
    if year_range is None:
        results = client.search(query, target_records=limit, topics=topics,year=2026)
    else:
        for year in range(year_range[0], year_range[1] + 1):
            results.extend(client.search(query, target_records=limit, topics=topics, year=year))

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
        "concepts": data.get("concepts", []),
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