"""Tests for scraper engine components."""
from __future__ import annotations

from decimal import Decimal
from pathlib import Path
from typing import Dict, Generator

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from core.db.base import Base
from core.db.repositories import ImageRepository, ProductRepository, StoreRepository
from core.scraper import detectors, extract_product_data, link_utils, run_scrape
from core.scraper.request_manager import RequestManager


FIXTURES = Path(__file__).parent / "fixtures" / "scraper"
PRODUCT_HTML = (FIXTURES / "product.html").read_text()
CATEGORY_HTML = (FIXTURES / "category.html").read_text()
START_HTML = (FIXTURES / "start.html").read_text()


class FakeRequestManager(RequestManager):
    """Request manager that returns canned HTML for tests."""

    def __init__(self, pages: Dict[str, str]):
        super().__init__(throttle_seconds=0)
        self.pages = pages

    def fetch(self, url: str) -> str:  # type: ignore[override]
        return self.pages[url]


@pytest.fixture()
def db_session() -> Generator[Session, None, None]:
    engine = create_engine("sqlite:///:memory:")
    TestingSessionLocal = sessionmaker(bind=engine)
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


def test_detectors_and_extractors() -> None:
    assert detectors.detect_product_page(PRODUCT_HTML)
    assert detectors.detect_category_page(CATEGORY_HTML)

    data = extract_product_data(PRODUCT_HTML, "http://example.com/product-a.html")
    assert data["name"] == "Sample Product"
    assert data["price"] == Decimal("19.99")
    assert data["currency"] == "USD"
    assert data["sku"] == "ABC123"
    assert data["category"] == "Gadgets"
    assert len(data["images"]) == 2


def test_link_utils_extracts_and_filters_links() -> None:
    links = link_utils.extract_links(CATEGORY_HTML, "http://example.com/category.html")
    assert "http://example.com/product-a.html" in links
    assert all(link_utils.is_same_domain(link, "example.com") for link in links)


def test_run_scrape_creates_products(db_session: Session) -> None:
    store_repo = StoreRepository(db_session)
    product_repo = ProductRepository(db_session)
    image_repo = ImageRepository(db_session)

    store = store_repo.create(name="Store A", theme="default", payment_provider=None)

    pages = {
        "http://example.com/index.html": START_HTML,
        "http://example.com/category.html": CATEGORY_HTML,
        "http://example.com/product-a.html": PRODUCT_HTML,
    }
    request_manager = FakeRequestManager(pages)

    created = run_scrape(
        "http://example.com/index.html",
        store_id=store.id,
        db=db_session,
        request_manager=request_manager,
        max_pages=10,
    )

    assert len(created) == 1
    product = product_repo.get_all()[0]
    assert product.name == "Sample Product"
    assert product.price == Decimal("19.99")
    assert product.category == "Gadgets"

    images = image_repo.get_by_product(product.id)
    assert [img.url for img in images] == [
        "http://example.com/images/prod1.jpg",
        "http://example.com/images/prod1-side.jpg",
    ]
