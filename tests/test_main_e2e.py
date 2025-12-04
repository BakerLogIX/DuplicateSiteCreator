"""End-to-end smoke test covering the main application wiring."""
from __future__ import annotations

from decimal import Decimal
from pathlib import Path

from core.config.settings import get_db_url
from core.db.base import SessionLocal
from core.db.repositories import (
    OrderItemRepository,
    OrderRepository,
    ProductRepository,
    StoreRepository,
    SupplierRepository,
)
from core.dropship.adapters.dummy_api import DummySupplierAdapter
from core.dropship.order_processor import FULFILLED_STATUS, process_pending_orders
from core.storegen.builder import build_store
from core.pricing.engine import run_pricing
from main import bootstrap_application


def _reset_database() -> None:
    url = get_db_url()
    if not url.startswith("sqlite"):
        return

    db_path = Path(url.split("sqlite:///")[-1])
    if not db_path.is_absolute():
        db_path = Path.cwd() / db_path

    if db_path.exists():
        db_path.unlink()


def test_end_to_end_smoke(tmp_path: Path) -> None:
    """Exercise a happy-path flow without launching the GUI."""

    _reset_database()

    context = bootstrap_application(
        env="test", enable_schedulers=False, launch_gui=False, store_name="E2E Store"
    )
    store_id = context["store_id"]

    session = SessionLocal()
    try:
        store_repo = StoreRepository(session)
        product_repo = ProductRepository(session)
        supplier_repo = SupplierRepository(session)
        order_repo = OrderRepository(session)
        order_item_repo = OrderItemRepository(session)

        store = store_repo.get_by_id(store_id)

        product = product_repo.create(
            store_id=store.id,
            name="Demo Product",
            price=Decimal("10.00"),
            currency=store.default_currency,
            category="Widgets",
            inventory_count=5,
        )

        supplier = supplier_repo.create(
            store_id=store.id, name="Acme Supplies", api_endpoint="https://example.test"
        )

        order = order_repo.create(
            store_id=store.id,
            total_amount=Decimal("10.00"),
            currency=store.default_currency,
            customer_name="Test Customer",
            customer_email="customer@example.test",
        )
        order_item_repo.create(
            order_id=order.id,
            product_id=product.id,
            supplier_id=None,
            quantity=1,
            unit_price=product.price,
            total_price=product.price,
        )

        priced_products = run_pricing(store_id, db=session)
        assert priced_products[0].price != Decimal("0")

        output_paths = build_store(store_id, output_dir=tmp_path, db=session)
        assert (tmp_path / "index.html").exists()
        assert output_paths

        processed = process_pending_orders(db=session, adapter=DummySupplierAdapter())
        assert processed and processed[0].status == FULFILLED_STATUS
        assert processed[0].tracking_number
    finally:
        session.close()
