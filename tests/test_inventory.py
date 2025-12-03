from decimal import Decimal
from typing import Generator

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from core.db.base import Base
from core.db.repositories import ProductRepository, StoreRepository, SupplierRepository, VariantRepository
from core.inventory.sync_service import start_inventory_sync_scheduler, sync_supplier_inventory


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


def test_sync_supplier_inventory_updates_products_and_variants(db_session: Session) -> None:
    store = StoreRepository(db_session).create(name="Store A", theme="default", payment_provider=None)
    supplier = SupplierRepository(db_session).create(store_id=store.id, name="Supplier")
    product = ProductRepository(db_session).create(
        store_id=store.id,
        name="Hiking Backpack",
        price=Decimal("75.00"),
        currency="USD",
        supplier_price=Decimal("50.00"),
        inventory_count=2,
    )
    variant = VariantRepository(db_session).create(
        product_id=product.id,
        name="Standard",
        price=Decimal("75.00"),
        inventory_count=2,
    )

    def fake_fetcher(_supplier):
        return [
            {
                "product_id": product.id,
                "variant_id": variant.id,
                "quantity": 8,
                "supplier_price": Decimal("60.00"),
            }
        ]

    pricing_updates = sync_supplier_inventory(supplier.id, db=db_session, fetcher=fake_fetcher)

    updated_product = ProductRepository(db_session).get_by_id(product.id)
    updated_variant = VariantRepository(db_session).get_by_id(variant.id)

    assert updated_product.inventory_count == 8
    assert updated_product.supplier_price == Decimal("60.00")
    assert updated_product.pricing_outdated is True
    assert updated_variant.inventory_count == 8

    assert pricing_updates == [product.id]


def test_sync_supplier_inventory_respects_threshold(db_session: Session) -> None:
    store = StoreRepository(db_session).create(name="Store B", theme="default", payment_provider=None)
    supplier = SupplierRepository(db_session).create(store_id=store.id, name="Supplier")
    product = ProductRepository(db_session).create(
        store_id=store.id,
        name="Trail Shoes",
        price=Decimal("90.00"),
        currency="USD",
        supplier_price=Decimal("50.00"),
        inventory_count=5,
        pricing_outdated=False,
    )

    def small_change_fetcher(_supplier):
        return [{"product_id": product.id, "quantity": 6, "supplier_price": Decimal("51.50")}]  # 3% change

    pricing_updates = sync_supplier_inventory(
        supplier.id, db=db_session, fetcher=small_change_fetcher, price_change_threshold=0.05
    )

    updated_product = ProductRepository(db_session).get_by_id(product.id)
    assert updated_product.inventory_count == 6
    assert updated_product.supplier_price == Decimal("51.50")
    assert updated_product.pricing_outdated is False
    assert pricing_updates == []


class DummyScheduler:
    def __init__(self) -> None:
        self.jobs = []
        self.started = False

    def add_job(self, func, trigger, minutes, args=None, kwargs=None, id=None, replace_existing=None):
        self.jobs.append(
            {
                "func": func,
                "trigger": trigger,
                "minutes": minutes,
                "args": args or [],
                "kwargs": kwargs or {},
                "id": id,
                "replace_existing": replace_existing,
            }
        )

    def start(self) -> None:
        self.started = True


def test_start_inventory_sync_scheduler_registers_jobs() -> None:
    scheduler = DummyScheduler()
    supplier_ids = [1, 2]

    start_inventory_sync_scheduler(interval_minutes=15, supplier_ids=supplier_ids, scheduler=scheduler)

    assert scheduler.started is True
    assert [job["id"] for job in scheduler.jobs] == ["sync_inventory_1", "sync_inventory_2"]
    assert all(job["func"] == sync_supplier_inventory for job in scheduler.jobs)
