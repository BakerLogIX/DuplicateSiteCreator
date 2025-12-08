"""Crawl a domain and persist detected products to the database."""
from __future__ import annotations

from collections import deque
from time import perf_counter
from typing import Dict, Optional, Set
from urllib.parse import urlparse

from sqlalchemy.orm import Session

from core.db.base import SessionLocal
from core.db.repositories import ImageRepository, ProductRepository, StoreRepository
from core.logging.logger import get_logger
from core.metrics import get_collector
from core.scraper.detectors import is_product_page
from core.scraper.extractors import extract_product_data
from core.scraper.link_utils import extract_links, is_same_domain
from core.scraper.request_manager import RequestManager

LOGGER = get_logger(__name__)


def run_scrape(
    start_url: str,
    store_id: int,
    *,
    max_pages: int = 100,
    request_manager: Optional[RequestManager] = None,
    db: Optional[Session] = None,
) -> Dict[str, int]:
    """Perform a breadth-first crawl of a domain and save discovered products."""

    session = db or SessionLocal()
    created_session = db is None
    try:
        collector = get_collector()
        store = StoreRepository(session).get_by_id(store_id)
        if not store:
            raise ValueError(f"Store with id {store_id} not found")

        product_repo = ProductRepository(session)
        image_repo = ImageRepository(session)
        rm = request_manager or RequestManager()

        parsed = urlparse(start_url)
        base_domain = parsed.netloc
        queue = deque([start_url])
        visited: Set[str] = set()
        products_created = 0
        started_at = perf_counter()

        while queue and len(visited) < max_pages:
            url = queue.popleft()
            if url in visited:
                continue
            visited.add(url)

            html = rm.fetch(url)
            if not html:
                continue

            if is_product_page(html):
                data = extract_product_data(html, url)
                existing = None
                if data.get("sku"):
                    existing = product_repo.get_by_sku(data["sku"], store_id=store_id)
                if existing:
                    product_repo.update(
                        existing,
                        name=data["name"],
                        price=data["price"],
                        description=data["description"],
                        category=data["category"],
                    )
                    product = existing
                else:
                    product = product_repo.create(
                        store_id=store_id,
                        name=data["name"],
                        price=data["price"],
                        description=data["description"],
                        category=data["category"],
                        sku=data.get("sku"),
                        currency=store.default_currency or "USD",
                    )
                    products_created += 1

                for position, src in enumerate(data.get("images", []), start=1):
                    image_repo.create(product_id=product.id, url=src, position=position)
            else:
                for link in extract_links(html, url):
                    if is_same_domain(link, base_domain) and link not in visited:
                        queue.append(link)

        duration = perf_counter() - started_at
        collector.increment("scraper.pages_visited", len(visited), store_id=store_id)
        collector.increment("scraper.products_discovered", products_created, store_id=store_id)
        collector.observe("scraper.duration_seconds", duration, store_id=store_id)

        return {"visited": len(visited), "products": products_created}
    finally:
        if created_session:
            session.close()


__all__ = ["run_scrape"]
