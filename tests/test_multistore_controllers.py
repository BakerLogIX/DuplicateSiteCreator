"""Tests for controller-level store isolation and settings updates."""
from __future__ import annotations

from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.controllers.orders_controller import OrdersController
from app.controllers.products_controller import ProductsController
from app.controllers.settings_controller import SettingsController
from core.db.base import Base
from core.db.repositories import OrderRepository, ProductRepository
from core.store_manager import StoreManager


def _setup_db() -> Session:
    engine = create_engine("sqlite:///:memory:")
    TestingSessionLocal = sessionmaker(bind=engine)
    Base.metadata.create_all(bind=engine)
    return TestingSessionLocal()


def test_controllers_default_to_current_store() -> None:
    db = _setup_db()
    try:
        store_manager = StoreManager(db)
        store_a = store_manager.create_store(name="Store A")
        store_b = store_manager.create_store(name="Store B")

        product_repo = ProductRepository(db)
        order_repo = OrderRepository(db)
        product_repo.create(store_id=store_a.id, name="A1", price=10, currency="USD")
        product_repo.create(store_id=store_b.id, name="B1", price=12, currency="USD")
        order_repo.create(store_id=store_a.id, total_amount=10, currency="USD")
        order_repo.create(store_id=store_b.id, total_amount=12, currency="USD")

        products_controller = ProductsController(db, store_manager=store_manager)
        orders_controller = OrdersController(db, store_manager=store_manager)

        store_manager.set_current_store(store_b.id)
        assert [p.name for p in products_controller.list_products()] == ["B1"]
        assert [o.total_amount for o in orders_controller.list_orders()] == [12]

        store_manager.set_current_store(store_a.id)
        assert [p.name for p in products_controller.list_products()] == ["A1"]
        assert [float(o.total_amount) for o in orders_controller.list_orders()] == [10.0]
    finally:
        db.close()


def test_settings_controller_updates_store_fields() -> None:
    db = _setup_db()
    try:
        store_manager = StoreManager(db)
        store = store_manager.create_store(name="Main", theme="default", default_currency="USD")
        controller = SettingsController(store_manager=store_manager)

        initial = controller.load_store_settings(store.id)
        assert initial["theme"] == "default"
        assert initial["default_currency"] == "USD"

        updated = controller.update_store_settings(
            store.id,
            theme="modern",
            payment_provider="stripe",
            default_currency="EUR",
            timezone="Europe/Paris",
        )

        assert updated["theme"] == "modern"
        assert updated["payment_provider"] == "stripe"
        assert updated["default_currency"] == "EUR"
        assert updated["timezone"] == "Europe/Paris"

        refreshed = controller.load_store_settings(store.id)
        assert refreshed == updated
    finally:
        db.close()
