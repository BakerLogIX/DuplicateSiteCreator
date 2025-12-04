from __future__ import annotations

from typing import Generator

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from core.db.base import Base
from core.db.repositories import ImageRepository, ProductRepository, StoreRepository
from core.scraper.detectors import is_category_page, is_product_page
from core.scraper.extractors import extract_product_data
from core.scraper.link_utils import extract_links, is_same_domain, normalize_url
from core.scraper.orchestrator import run_scrape


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


@pytest.fixture()
def sample_product_html() -> str:
    return """
    <html>
        <head>
            <title>Trail Runner</title>
            <meta property="og:title" content="Trail Runner">
            <meta name="product:price:amount" content="129.99">
            <meta name="product:retailer_item_id" content="SKU-TRAIL-1">
            <meta name="product:category" content="Footwear">
        </head>
        <body>
            <nav class="breadcrumb"><span class="active">Footwear</span></nav>
            <h1 class="product-title">Trail Runner</h1>
            <div class="product-price">$129.99</div>
            <button>Add to Cart</button>
            <div class="product-description">Durable trail running shoe</div>
            <img src="http://example.com/images/trail.jpg" />
        </body>
    </html>
    """


def test_link_utils_normalize_and_same_domain() -> None:
    base = "https://example.com/shop/index.html"
    href = "../product/1#details"
    normalized = normalize_url(href, base)
    assert normalized == "https://example.com/product/1"
    assert is_same_domain(normalized, "example.com")
    other = normalize_url("https://external.com/page", base)
    assert other == "https://external.com/page"
    assert not is_same_domain(other, "example.com")


def test_extract_links_deduplicates_and_normalizes() -> None:
    html = """
    <a href="/p1">Product</a>
    <a href="/p1#section">Product again</a>
    <a href="javascript:void(0)">ignore</a>
    """
    links = extract_links(html, "https://example.com")
    assert links == ["https://example.com/p1"]


def test_detectors_and_extractors(sample_product_html: str) -> None:
    assert is_product_page(sample_product_html)
    assert not is_category_page(sample_product_html)
    data = extract_product_data(sample_product_html, "https://example.com/product/trail")
    assert data["name"] == "Trail Runner"
    assert float(data["price"]) == pytest.approx(129.99)
    assert data["category"] == "Footwear"
    assert data["sku"] == "SKU-TRAIL-1"
    assert "trail.jpg" in data["images"][0]


def test_orchestrator_crawls_and_saves_products(sample_product_html: str, db_session: Session) -> None:
    start_url = "http://example.com"
    product_url = "http://example.com/product/trail"
    listing_html = f'<a href="{product_url}">Trail</a><a href="http://other.com">Skip</a>'

    class FakeRequestManager:
        def __init__(self, pages):
            self.pages = pages

        def fetch(self, url: str):
            return self.pages.get(url)

    rm = FakeRequestManager({start_url: listing_html, product_url: sample_product_html})

    store = StoreRepository(db_session).create(name="Demo", theme="default", payment_provider=None)

    result = run_scrape(start_url, store.id, request_manager=rm, db=db_session)

    assert result["products"] == 1
    product_repo = ProductRepository(db_session)
    products = product_repo.get_by_store(store.id)
    assert len(products) == 1
    product = products[0]
    assert product.name == "Trail Runner"
    images = ImageRepository(db_session).get_by_product(product.id)
    assert images and "trail.jpg" in images[0].url
