import logging

import requests

from app.config import SERP_API_KEY, MAX_SEARCH_RESULTS

logger = logging.getLogger(__name__)

SERPAPI_URL = "https://serpapi.com/search"


def search_google(query: str, num_results: int = MAX_SEARCH_RESULTS) -> list[str]:
    """
    Search Google via SerpAPI and return a list of result URLs.
    Returns an empty list if the API key is not configured or the request fails.
    """
    if not SERP_API_KEY:
        logger.warning("[search_engine] SERP_API_KEY not set — web search disabled.")
        return []

    params = {
        "q": query,
        "api_key": SERP_API_KEY,
        "engine": "google",
        "num": num_results,
    }

    try:
        response = requests.get(SERPAPI_URL, params=params, timeout=15)
        response.raise_for_status()
        data = response.json()
    except Exception as exc:
        logger.error(f"[search_engine] SerpAPI request failed: {exc}")
        return []

    urls = [
        result["link"]
        for result in data.get("organic_results", [])
        if "link" in result
    ]

    logger.info(f"[search_engine] Found {len(urls)} URLs for query: '{query}'")
    return urls[:num_results]


