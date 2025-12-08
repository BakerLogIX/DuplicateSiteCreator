"""Services for synchronising supplier inventory into local products."""
from __future__ import annotations

from decimal import Decimal
from typing import Callable, Iterable, List, Optional, Sequence

from sqlalchemy.orm import Session

from core.db.base import SessionLocal
from core.db.repositories import ProductRepository, SupplierRepository, VariantRepository
from core.logging.logger import get_logger
from core.metrics import get_collector
from core.models.entities import Supplier

try:  # pragma: no cover - optional dependency for scheduling
    from apscheduler.schedulers.background import BackgroundScheduler
except ImportError:  # pragma: no cover
    BackgroundScheduler = None

LOGGER = get_logger(__name__)

InventoryFetcher = Callable[[Supplier], Sequence[dict]]


def _default_inventory_fetcher(_: Supplier) -> Sequence[dict]:
    """Return an empty inventory list when no fetcher is provided."""

    return []


def _price_changed_significantly(old: Optional[Decimal], new: Decimal, threshold: float) -> bool:
    if old is None:
        return True
    if old == 0:
        return True
    difference = abs(new - old)
    return (difference / abs(old)) >= Decimal(str(threshold))


def sync_supplier_inventory(
    supplier_id: int,
    *,
    db: Optional[Session] = None,
    fetcher: Optional[InventoryFetcher] = None,
    price_change_threshold: float = 0.05,
) -> List[int]:
    """Synchronise inventory and supplier pricing for a supplier's products.

    Args:
        supplier_id: Identifier of the supplier to synchronise.
        db: Optional SQLAlchemy session. If omitted, a new session is created.
        fetcher: Callable that returns supplier inventory records. Each record may
            include ``product_id``, optional ``variant_id``, ``quantity`` and
            ``supplier_price`` keys.
        price_change_threshold: Fractional threshold for flagging pricing updates.

    Returns:
        List of product IDs whose supplier price changed beyond the threshold.
    """

    close_session = False
    if db is None:
        db = SessionLocal()
        close_session = True

    product_repo = ProductRepository(db)
    supplier_repo = SupplierRepository(db)
    variant_repo = VariantRepository(db)
    fetch_inventory: InventoryFetcher = fetcher or _default_inventory_fetcher
    pricing_updates: List[int] = []
    collector = get_collector()

    try:
        supplier = supplier_repo.get_by_id(supplier_id)
        if not supplier:
            raise ValueError(f"Supplier with id {supplier_id} not found")

        store_id = supplier.store_id
        records = list(fetch_inventory(supplier))
        collector.increment("inventory.sync_runs", 1, store_id=store_id)
        collector.increment("inventory.records_processed", len(records), store_id=store_id)

        for record in records:
            product_id = record.get("product_id")
            variant_id = record.get("variant_id")
            quantity = record.get("quantity")
            supplier_price = record.get("supplier_price")

            product = product_repo.get_by_id(product_id) if product_id else None
            if not product:
                LOGGER.warning("Inventory record references missing product %s", product_id)
                continue

            if variant_id:
                variant = variant_repo.get_by_id(variant_id)
                if not variant or variant.product_id != product.id:
                    LOGGER.warning(
                        "Variant %s missing or mismatched for product %s", variant_id, product.id
                    )
                else:
                    updates = {}
                    if quantity is not None:
                        updates["inventory_count"] = quantity
                    if supplier_price is not None:
                        updates["price"] = Decimal(str(supplier_price))
                    if updates:
                        variant_repo.update(variant, **updates)

            product_updates = {}
            if quantity is not None:
                product_updates["inventory_count"] = quantity
            if supplier_price is not None:
                new_price = Decimal(str(supplier_price))
                old_price = Decimal(product.supplier_price) if product.supplier_price else None
                product_updates["supplier_price"] = new_price
                product_updates["pricing_outdated"] = _price_changed_significantly(
                    old_price, new_price, price_change_threshold
                )
                if product_updates["pricing_outdated"]:
                    pricing_updates.append(product.id)

            if product_updates:
                product_repo.update(product, **product_updates)

        collector.increment("inventory.products_flagged", len(pricing_updates), store_id=store_id)
        return pricing_updates
    finally:
        if close_session:
            db.close()


def start_inventory_sync_scheduler(
    interval_minutes: int = 60,
    supplier_ids: Optional[Iterable[int]] = None,
    scheduler: Optional["BackgroundScheduler"] = None,
    fetcher: Optional[InventoryFetcher] = None,
    store_id: Optional[int] = None,
    db: Optional[Session] = None,
) -> "BackgroundScheduler":
    """Start periodic inventory synchronisation jobs for suppliers.

    If ``store_id`` is provided, only active suppliers for that store are scheduled
    when ``supplier_ids`` is not explicitly supplied. A database session can be
    provided to reuse caller-managed transactions.
    """

    if scheduler is None and BackgroundScheduler is None:  # pragma: no cover - dependency guard
        raise ImportError("APScheduler is required to start the inventory scheduler.")

    scheduler = scheduler or BackgroundScheduler()
    ids = list(supplier_ids) if supplier_ids is not None else []
    close_session = False
    session = db
    if not ids:
        if session is None:
            session = SessionLocal()
            close_session = True
        try:
            ids = [
                supplier.id
                for supplier in SupplierRepository(session).get_active_suppliers(store_id=store_id)
            ]
        finally:
            if close_session and session is not None:
                session.close()

    for supplier_id in ids:
        scheduler.add_job(
            sync_supplier_inventory,
            "interval",
            minutes=interval_minutes,
            args=[supplier_id],
            kwargs={"fetcher": fetcher},
            id=f"sync_inventory_{supplier_id}",
            replace_existing=True,
        )

    scheduler.start()
    LOGGER.info(
        "Inventory synchronisation scheduled every %s minutes for suppliers %s",
        interval_minutes,
        ids,
    )
    return scheduler
