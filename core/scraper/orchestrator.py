"""Scraper orchestrator to crawl a domain and persist products."""
from __future__ import annotations

from collections import deque
from decimal import Decimal
from typing import List, Optional, Set
from urllib.parse import urlparse

from sqlalchemy.orm import Session

from core.config.settings import get_default_currency
from core.db.base import SessionLocal
from core.db.repositories import ImageRepository, ProductRepository
from core.scraper import detectors, extractors, link_utils
from core.scraper.request_manager import RequestManager


def _ensure_decimal(value: object) -> Optional[Decimal]:
    if isinstance(value, Decimal):
        return value
    if value is None:
        return None
    try:
        return Decimal(str(value))
    except Exception:
        return None


def run_scrape(
    start_url: str,
    store_id: int,
    *,
    db: Optional[Session] = None,
    request_manager: Optional[RequestManager] = None,
    max_pages: int = 100,
) -> List[object]:
    """Crawl ``start_url`` and persist detected products for the store."""

    local_session = db is None
    session = db or SessionLocal()
    req = request_manager or RequestManager()
    created_products = []

    parsed_start = urlparse(start_url)
    base_domain = parsed_start.netloc

    queue: deque[str] = deque([start_url])
    visited: Set[str] = set()

    product_repo = ProductRepository(session)
    image_repo = ImageRepository(session)
    default_currency = get_default_currency()

    try:
        while queue and len(visited) < max_pages:
            url = queue.popleft()
            if url in visited:
                continue
            visited.add(url)

            try:
                html = req.fetch(url)
            except Exception:
                continue

            for link in link_utils.extract_links(html, url):
                if link_utils.is_same_domain(link, base_domain) and link not in visited:
                    queue.append(link)

            if not detectors.detect_product_page(html):
                continue

            data = extractors.extract_product_data(html, url)
            name = data.get("name")
            price = _ensure_decimal(data.get("price"))
            currency = data.get("currency") or default_currency

            if not name or price is None:
                continue

            existing = None
            sku = data.get("sku")
            if sku:
                existing = product_repo.get_by_sku(sku)
                if existing and existing.store_id != store_id:
                    existing = None

            if existing:
                product = product_repo.update(
                    existing,
                    name=name,
                    price=price,
                    currency=currency,
                    description=data.get("description"),
                    category=data.get("category"),
                )
            else:
                product = product_repo.create(
                    store_id=store_id,
                    name=name,
                    price=price,
                    currency=currency,
                    description=data.get("description"),
                    category=data.get("category"),
                    sku=sku,
                )

            for position, img_url in enumerate(data.get("images", [])):
                image_repo.create(
                    product_id=product.id,
                    url=img_url,
                    alt_text=f"{name} image {position + 1}",
                    position=position,
                )

            created_products.append(product)
    finally:
        if local_session:
            session.close()

    return created_products
