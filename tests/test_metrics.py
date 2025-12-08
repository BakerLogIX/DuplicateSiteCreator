"""Metrics collector and instrumentation tests."""
from __future__ import annotations

from decimal import Decimal
from typing import Generator

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from core.db.base import Base
from core.db.repositories import (
    OrderItemRepository,
    OrderRepository,
    ProductRepository,
    StoreRepository,
    SupplierRepository,
)
from core.dropship.adapters import DummySupplierAdapter
from core.dropship.order_processor import process_pending_orders
from core.metrics.collector import get_collector
from core.pricing.engine import run_pricing


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


def test_metrics_collector_basic_counts() -> None:
    collector = get_collector()
    collector.reset()

    collector.increment("demo.counter", 2, store_id=1)
    collector.observe("demo.measure", 5.0, store_id=1)

    snapshot = collector.get_snapshot(1)
    assert snapshot["counters"]["demo.counter"] == 2
    measure = snapshot["measurements"]["demo.measure"]
    assert measure.count == 1
    assert measure.avg == measure.minimum == measure.maximum == 5.0


def test_pricing_records_metrics(db_session: Session) -> None:
    collector = get_collector()
    collector.reset()

    store = StoreRepository(db_session).create(name="Store", theme="default", payment_provider=None)
    product_repo = ProductRepository(db_session)
    product_repo.create(store_id=store.id, name="Product", price=Decimal("10.00"), currency="USD")

    run_pricing(store.id, db=db_session)

    snapshot = collector.get_snapshot(store.id)
    assert snapshot["counters"]["pricing.products_processed"] == 1
    uplift_stats = snapshot["measurements"]["pricing.uplift_total"]
    assert uplift_stats.count == 1
    assert uplift_stats.avg > 0


def test_order_processing_records_metrics(db_session: Session) -> None:
    collector = get_collector()
    collector.reset()

    store_repo = StoreRepository(db_session)
    product_repo = ProductRepository(db_session)
    supplier_repo = SupplierRepository(db_session)
    order_repo = OrderRepository(db_session)
    order_item_repo = OrderItemRepository(db_session)

    store = store_repo.create(name="Store", theme="default", payment_provider=None)
    product = product_repo.create(store_id=store.id, name="Product", price=50, currency="USD")
    supplier_repo.create(store_id=store.id, name="Supplier", active=True)

    order = order_repo.create(store_id=store.id, total_amount=50, currency="USD")
    order_item_repo.create(
        order_id=order.id,
        product_id=product.id,
        variant_id=None,
        supplier_id=None,
        quantity=1,
        unit_price=50,
        total_price=50,
    )

    process_pending_orders(db_session, adapter=DummySupplierAdapter(), store_id=store.id)

    snapshot = collector.get_snapshot(store.id)
    assert snapshot["counters"]["orders.processed"] == 1
    assert snapshot["counters"]["orders.fulfilled"] == 1
