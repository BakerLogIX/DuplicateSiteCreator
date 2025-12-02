"""Scraper orchestrator that coordinates the crawl."""
from collections import deque
from typing import Iterable, List, Optional

from core.logging.logger import get_logger
from core.scraper.extractors import extract_product_data
from core.scraper.link_utils import extract_links
from core.scraper.request_manager import RequestManager

logger = get_logger(__name__)


def run_scrape(start_url: str, store_id: int, max_pages: int = 50) -> List[dict]:
    manager = RequestManager()
    visited = set()
    queue: deque[str] = deque([start_url])
    products: List[dict] = []

    while queue and len(visited) < max_pages:
        url = queue.popleft()
        if url in visited:
            continue
        visited.add(url)

        html = manager.fetch(url)
        if not html:
            continue

        product_data = extract_product_data(html, url)
        if product_data:
            product_data["store_id"] = store_id
            products.append(product_data)

        for link in extract_links(html, url):
            if link not in visited:
                queue.append(link)

    logger.info("Scrape complete. Discovered %s product candidates.", len(products))
    return products
