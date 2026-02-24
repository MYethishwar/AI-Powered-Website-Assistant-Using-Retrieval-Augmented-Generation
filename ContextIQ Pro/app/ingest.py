import logging
from urllib.parse import urlparse

from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.config import CHUNK_SIZE, CHUNK_OVERLAP, MAX_CRAWL_PAGES
from app.scraping import fetch_page_and_links

logger = logging.getLogger(__name__)

_splitter = RecursiveCharacterTextSplitter(
    chunk_size=CHUNK_SIZE,
    chunk_overlap=CHUNK_OVERLAP,
)


def _make_chunks(text: str, source_url: str) -> list[dict]:
    """Split text and attach source metadata to each chunk."""
    raw_chunks = _splitter.split_text(text)
    return [{"text": chunk, "source": source_url} for chunk in raw_chunks if chunk.strip()]


def ingest_pages(
    seed_urls: list[str],
    max_pages: int = MAX_CRAWL_PAGES,
) -> list[dict]:
    """
    BFS crawl starting from seed_urls.
    Returns a list of {"text": ..., "source": ...} dicts.
    Only crawls pages within the same domain as each seed URL.
    """
    # Determine allowed domains from seeds
    allowed_domains = {urlparse(u).netloc for u in seed_urls}

    visited: set[str] = set()
    queue: list[str] = list(seed_urls)
    all_chunks: list[dict] = []

    while queue and len(visited) < max_pages:
        url = queue.pop(0)

        if url in visited:
            continue

        # Skip URLs outside allowed domains
        if urlparse(url).netloc not in allowed_domains:
            continue

        logger.info(f"[crawl] Fetching ({len(visited)+1}/{max_pages}): {url}")
        text, links = fetch_page_and_links(url)
        visited.add(url)

        if not text.strip():
            logger.warning(f"[crawl] Empty content at {url}, skipping.")
            continue

        chunks = _make_chunks(text, source_url=url)
        all_chunks.extend(chunks)
        logger.info(f"[crawl] Got {len(chunks)} chunks from {url}")

        # Enqueue new unvisited links (filter by domain again just in case)
        for link in links:
            if link not in visited and urlparse(link).netloc in allowed_domains:
                queue.append(link)

    logger.info(f"[crawl] Done. {len(visited)} pages scraped, {len(all_chunks)} total chunks.")
    return all_chunks


