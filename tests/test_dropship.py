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


def test_process_pending_orders_scopes_by_store(db_session: Session) -> None:
    store_repo = StoreRepository(db_session)
    product_repo = ProductRepository(db_session)
    supplier_repo = SupplierRepository(db_session)
    order_repo = OrderRepository(db_session)
    order_item_repo = OrderItemRepository(db_session)

    store_a = store_repo.create(name="Store A", theme="default", payment_provider=None)
    store_b = store_repo.create(name="Store B", theme="default", payment_provider=None)

    product_a = product_repo.create(store_id=store_a.id, name="Product A", price=25, currency="USD")
    product_b = product_repo.create(store_id=store_b.id, name="Product B", price=30, currency="USD")
    supplier_a = supplier_repo.create(store_id=store_a.id, name="Supplier A", active=True)

    order_a = order_repo.create(store_id=store_a.id, total_amount=25, currency="USD")
    order_item_repo.create(
        order_id=order_a.id,
        product_id=product_a.id,
        supplier_id=None,
        variant_id=None,
        quantity=1,
        unit_price=25,
        total_price=25,
    )

    order_b = order_repo.create(store_id=store_b.id, total_amount=30, currency="USD")
    order_item_repo.create(
        order_id=order_b.id,
        product_id=product_b.id,
        supplier_id=None,
        variant_id=None,
        quantity=1,
        unit_price=30,
        total_price=30,
    )

    processed = process_pending_orders(
        db_session, adapter=DummySupplierAdapter(), store_id=store_a.id
    )

    assert {o.id for o in processed} == {order_a.id}

    refreshed_a = order_repo.get_by_id(order_a.id)
    refreshed_b = order_repo.get_by_id(order_b.id)
    assert refreshed_a.status == FULFILLED_STATUS
    assert refreshed_b.status == "pending"

    items_a = order_item_repo.get_by_order(order_a.id)
    items_b = order_item_repo.get_by_order(order_b.id)
    assert items_a[0].supplier_id == supplier_a.id
    assert items_a[0].tracking_number
    assert items_b[0].status == "pending"
    assert items_b[0].supplier_id is None
