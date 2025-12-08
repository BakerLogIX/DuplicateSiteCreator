"""Unit tests for repository CRUD operations and store isolation."""
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
    PriceRuleRepository,
    ProductRepository,
    StoreRepository,
    SupplierRepository,
    TransactionRepository,
    VariantRepository,
)


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


def test_product_crud_and_store_isolation(db_session: Session) -> None:
    store_repo = StoreRepository(db_session)
    product_repo = ProductRepository(db_session)

    store_a = store_repo.create(name="Store A", theme="default", payment_provider=None)
    store_b = store_repo.create(name="Store B", theme="default", payment_provider=None)

    assert store_repo.get_by_name("Store A") == store_a

    prod_a1 = product_repo.create(
        store_id=store_a.id,
        name="Product A1",
        price=Decimal("19.99"),
        currency="USD",
    )
    prod_a2 = product_repo.create(
        store_id=store_a.id,
        name="Product A2",
        price=Decimal("25.00"),
        currency="USD",
        is_active=False,
    )
    prod_b1 = product_repo.create(
        store_id=store_b.id, name="Product B1", price=Decimal("29.99"), currency="USD"
    )

    assert product_repo.get_by_id(prod_a1.id).name == "Product A1"

    updated = product_repo.update(prod_a1, name="Product A1 Updated")
    assert updated.name == "Product A1 Updated"

    store_a_products = product_repo.get_by_store(store_a.id)
    assert {p.id for p in store_a_products} == {prod_a1.id, prod_a2.id}
    assert {p.id for p in product_repo.get_by_store(store_b.id)} == {prod_b1.id}

    active_store_a_products = product_repo.get_active_by_store(store_a.id)
    assert [p.id for p in active_store_a_products] == [prod_a1.id]

    all_products = product_repo.get_all()
    assert {p.id for p in all_products} == {prod_a1.id, prod_a2.id, prod_b1.id}

    product_repo.delete(prod_b1)
    assert product_repo.get_by_id(prod_b1.id) is None


def test_variant_and_supplier_relationships(db_session: Session) -> None:
    store_repo = StoreRepository(db_session)
    product_repo = ProductRepository(db_session)
    variant_repo = VariantRepository(db_session)
    supplier_repo = SupplierRepository(db_session)

    store = store_repo.create(name="Store A", theme="default", payment_provider=None)
    product = product_repo.create(store_id=store.id, name="Product", price=10, currency="USD")

    _ = variant_repo.create(product_id=product.id, name="Red", price=12, inventory_count=5)
    variant_repo.create(product_id=product.id, name="Blue", price=11, inventory_count=3)

    suppliers = [
        supplier_repo.create(store_id=store.id, name="Supplier 1"),
        supplier_repo.create(store_id=store.id, name="Supplier 2", active=False),
    ]
    other_store = store_repo.create(name="Store B", theme="default", payment_provider=None)
    supplier_repo.create(store_id=other_store.id, name="Supplier 3")

    variants = variant_repo.get_by_product(product.id)
    assert {v.name for v in variants} == {"Red", "Blue"}

    active_suppliers = supplier_repo.get_active_suppliers(store.id)
    assert [s.name for s in active_suppliers] == [suppliers[0].name]

    suppliers_for_store = supplier_repo.get_by_store(store.id)
    assert {s.name for s in suppliers_for_store} == {"Supplier 1", "Supplier 2"}



def test_product_lookup_by_sku_is_store_scoped(db_session: Session) -> None:
    store_repo = StoreRepository(db_session)
    product_repo = ProductRepository(db_session)

    store_a = store_repo.create(name="Store A", theme="default", payment_provider=None)
    store_b = store_repo.create(name="Store B", theme="default", payment_provider=None)

    product = product_repo.create(
        store_id=store_a.id, name="Product", price=20, currency="USD", sku="SKU-123"
    )
    product_repo.create(store_id=store_b.id, name="Other", price=30, currency="USD", sku="SKU-456")

    assert product_repo.get_by_sku("SKU-123", store_id=store_a.id).id == product.id
    assert product_repo.get_by_sku("SKU-123", store_id=store_b.id) is None
    # Backward-compatible lookup without store_id still returns the matching SKU.
    assert product_repo.get_by_sku("SKU-123").id == product.id


def test_orders_and_transactions(db_session: Session) -> None:
    store_repo = StoreRepository(db_session)
    product_repo = ProductRepository(db_session)
    order_repo = OrderRepository(db_session)
    order_item_repo = OrderItemRepository(db_session)
    transaction_repo = TransactionRepository(db_session)

    store = store_repo.create(name="Store A", theme="default", payment_provider=None)
    product = product_repo.create(store_id=store.id, name="Product", price=50, currency="USD")

    order = order_repo.create(store_id=store.id, total_amount=50, currency="USD")
    _ = order_repo.create(store_id=store.id, total_amount=75, currency="USD", status="complete")
    order_item_repo.create(
        order_id=order.id,
        product_id=product.id,
        variant_id=None,
        supplier_id=None,
        quantity=2,
        unit_price=25,
        total_price=50,
    )

    transaction_repo.create(
        store_id=store.id,
        order_id=order.id,
        amount=50,
        currency="USD",
        status="pending",
        transaction_type="charge",
    )

    pending = order_repo.get_pending_orders(store_id=store.id)
    assert [o.id for o in pending] == [order.id]

    items = order_item_repo.get_by_order(order.id)
    assert len(items) == 1
    assert items[0].quantity == 2

    transactions = transaction_repo.get_by_order(order.id)
    assert len(transactions) == 1
    assert transactions[0].amount == Decimal("50")
    assert [t.id for t in transaction_repo.get_by_store(store.id)] == [transactions[0].id]



def test_price_rules(db_session: Session) -> None:
    store_repo = StoreRepository(db_session)
    price_rule_repo = PriceRuleRepository(db_session)

    store = store_repo.create(name="Store A", theme="default", payment_provider=None)
    rule_active = price_rule_repo.create(
        store_id=store.id,
        name="Margin 10%",
        rule_type="margin",
        value=Decimal("10.00"),
        active=True,
    )
    price_rule_repo.create(
        store_id=store.id,
        name="Inactive rule",
        rule_type="margin",
        value=Decimal("5.00"),
        active=False,
    )

    all_rules = price_rule_repo.get_by_store(store.id)
    assert {r.id for r in all_rules} == {rule_active.id, rule_active.id + 1}

    active_rules = price_rule_repo.get_active_rules(store.id)
    assert [r.name for r in active_rules] == ["Margin 10%"]

    active_all_stores = price_rule_repo.get_active_rules()
    assert [r.id for r in active_all_stores] == [rule_active.id]
