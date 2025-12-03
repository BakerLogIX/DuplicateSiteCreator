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
from core.dropship.order_processor import (
    FAILED_STATUS,
    FULFILLED_STATUS,
    process_pending_orders,
)
from core.dropship.router import select_supplier


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


def test_select_supplier_picks_first_active_supplier(db_session: Session) -> None:
    store_repo = StoreRepository(db_session)
    product_repo = ProductRepository(db_session)
    supplier_repo = SupplierRepository(db_session)

    store = store_repo.create(name="Store", theme="default", payment_provider=None)
    product = product_repo.create(store_id=store.id, name="Product", price=10, currency="USD")

    supplier_repo.create(store_id=store.id, name="Inactive Supplier", active=False)
    active_supplier = supplier_repo.create(store_id=store.id, name="Active Supplier", active=True)

    selected = select_supplier(db_session, product.id)
    assert selected is not None
    assert selected.id == active_supplier.id


def test_process_pending_orders_assigns_supplier_and_tracking(
    db_session: Session,
) -> None:
    store_repo = StoreRepository(db_session)
    product_repo = ProductRepository(db_session)
    supplier_repo = SupplierRepository(db_session)
    order_repo = OrderRepository(db_session)
    order_item_repo = OrderItemRepository(db_session)

    store = store_repo.create(name="Store", theme="default", payment_provider=None)
    product = product_repo.create(store_id=store.id, name="Product", price=50, currency="USD")
    supplier = supplier_repo.create(store_id=store.id, name="Supplier", active=True)

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

    processed_orders = process_pending_orders(db_session, adapter=DummySupplierAdapter())

    assert processed_orders[0].status == FULFILLED_STATUS
    refreshed_items = order_item_repo.get_by_order(order.id)
    assert refreshed_items[0].supplier_id == supplier.id
    assert refreshed_items[0].tracking_number
    assert processed_orders[0].tracking_number == refreshed_items[0].tracking_number
    assert refreshed_items[0].status == FULFILLED_STATUS


def test_process_pending_orders_marks_failed_if_no_supplier(db_session: Session) -> None:
    store_repo = StoreRepository(db_session)
    product_repo = ProductRepository(db_session)
    order_repo = OrderRepository(db_session)
    order_item_repo = OrderItemRepository(db_session)

    store = store_repo.create(name="Store", theme="default", payment_provider=None)
    product = product_repo.create(store_id=store.id, name="Product", price=50, currency="USD")

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

    processed_orders = process_pending_orders(db_session, adapter=DummySupplierAdapter())

    assert processed_orders[0].status == FAILED_STATUS
    refreshed_items = order_item_repo.get_by_order(order.id)
    assert refreshed_items[0].status == FAILED_STATUS
    assert refreshed_items[0].tracking_number is None
