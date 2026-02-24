import logging
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout

logger = logging.getLogger(__name__)


def fetch_page_and_links(url: str) -> tuple[str, list[str]]:
    """
    Scrape a single page using Playwright and return (clean_text, internal_links).
    Returns ("", []) on failure instead of raising, so crawls can continue.
    """
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                user_agent=(
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/120.0.0.0 Safari/537.36"
                )
            )
            page = context.new_page()

            try:
                page.goto(url, wait_until="networkidle", timeout=60_000)
            except PlaywrightTimeout:
                # Fall back to domcontentloaded if networkidle times out
                logger.warning(f"networkidle timeout for {url}, retrying with domcontentloaded")
                page.goto(url, wait_until="domcontentloaded", timeout=30_000)

            html = page.content()
            browser.close()

    except Exception as exc:
        logger.error(f"Failed to fetch {url}: {exc}")
        return "", []

    soup = BeautifulSoup(html, "html.parser")

    # Strip non-content tags
    for tag in soup(["script", "style", "noscript", "header", "footer", "nav", "iframe"]):
        tag.decompose()

    # Extract same-domain links
    base_domain = urlparse(url).netloc
    links: set[str] = set()
    for anchor in soup.find_all("a", href=True):
        full_url = urljoin(url, anchor["href"])
        parsed = urlparse(full_url)
        # Only keep http/https links on the same domain, drop fragments/query noise
        if parsed.scheme in ("http", "https") and parsed.netloc == base_domain:
            # Normalise: strip fragment
            clean = parsed._replace(fragment="").geturl()
            links.add(clean)

    text = soup.get_text(separator="\n", strip=True)
    return text, list(links)


