from __future__ import annotations

from decimal import Decimal
from typing import Generator

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from core.db.base import Base
from core.db.repositories import ProductRepository, StoreRepository
from core.storegen.builder import build_store
from core.storegen.exporter import build_deployment_manifest, export_static_store


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


def test_build_store_generates_pages(tmp_path, db_session: Session) -> None:
    store_repo = StoreRepository(db_session)
    product_repo = ProductRepository(db_session)

    store = store_repo.create(name="Demo Store", theme="default", payment_provider=None)

    shoe = product_repo.create(
        store_id=store.id,
        name="Trail Runner",
        description="Durable trail running shoe",
        price=Decimal("120.00"),
        currency="USD",
        category="Footwear",
    )
    accessory = product_repo.create(
        store_id=store.id,
        name="Hydration Pack",
        description="Lightweight pack for long runs",
        price=Decimal("79.99"),
        currency="USD",
        category=None,
    )
    product_repo.create(
        store_id=store.id,
        name="Hidden Product",
        price=Decimal("50"),
        currency="USD",
        category="Footwear",
        is_active=False,
    )

    generated = build_store(store.id, tmp_path, db=db_session)

    home = tmp_path / "index.html"
    footwear = tmp_path / "category-footwear.html"
    uncategorized = tmp_path / "category-uncategorized.html"
    product_page = tmp_path / f"product-{shoe.id}.html"

    assert generated["home"] == home
    assert home.exists()
    assert footwear.exists()
    assert uncategorized.exists()
    assert product_page.exists()

    home_contents = home.read_text(encoding="utf-8")
    assert "Demo Store catalog" in home_contents
    assert "Trail Runner" in home_contents
    assert "Hydration Pack" in home_contents
    assert "Hidden Product" not in home_contents

    footwear_contents = footwear.read_text(encoding="utf-8")
    assert "Trail Runner" in footwear_contents
    assert "Hydration Pack" not in footwear_contents

    uncategorized_contents = uncategorized.read_text(encoding="utf-8")
    assert "Hydration Pack" in uncategorized_contents

    product_contents = product_page.read_text(encoding="utf-8")
    assert "Durable trail running shoe" in product_contents
    assert "Category: Footwear" in product_contents


def test_exporter_copies_store(tmp_path) -> None:
    source = tmp_path / "source"
    destination = tmp_path / "destination"
    source.mkdir()
    (source / "index.html").write_text("<h1>Store</h1>", encoding="utf-8")

    export_static_store(source, destination)
    assert (destination / "index.html").read_text(encoding="utf-8") == "<h1>Store</h1>"

    manifest = build_deployment_manifest(destination)
    assert manifest == {"index.html": (destination / "index.html").stat().st_size}
