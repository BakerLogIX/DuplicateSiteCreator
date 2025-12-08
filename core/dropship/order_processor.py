"""Order processing and scheduling utilities."""
from __future__ import annotations

from typing import List, Optional

from core.db.base import SessionLocal
from core.db.repositories import OrderItemRepository, OrderRepository
from core.dropship.adapters import DummySupplierAdapter, SupplierAdapter
from core.dropship.router import select_supplier
from core.logging.logger import get_logger
from core.metrics import get_collector
from core.models.entities import Order

try:  # pragma: no cover - optional dependency for scheduling
    from apscheduler.schedulers.background import BackgroundScheduler
except ImportError:  # pragma: no cover
    BackgroundScheduler = None


LOGGER = get_logger(__name__)


PENDING_STATUS = "pending"
PROCESSING_STATUS = "processing"
FULFILLED_STATUS = "fulfilled"
FAILED_STATUS = "failed"


def process_pending_orders(
    db=None, adapter: Optional[SupplierAdapter] = None, store_id: Optional[int] = None
) -> List[Order]:
    """Process pending orders by routing items to suppliers.

    Args:
        db: Optional SQLAlchemy session. If omitted, a new session is created.
        adapter: Supplier adapter used to communicate with suppliers. Defaults
            to the :class:`DummySupplierAdapter`.
        store_id: If provided, restrict processing to orders belonging to this store.

    Returns:
        A list of orders that were processed.
    """

    close_session = False
    if db is None:
        db = SessionLocal()
        close_session = True

    order_repo = OrderRepository(db)
    order_item_repo = OrderItemRepository(db)
    adapter = adapter or DummySupplierAdapter()
    collector = get_collector()
    processed_orders = []

    try:
        pending_orders = order_repo.get_pending_orders(store_id=store_id)
        for order in pending_orders:
            collector.increment("orders.processed", 1, store_id=order.store_id)
        for order in pending_orders:
            order.status = PROCESSING_STATUS
            db.add(order)
            db.commit()
            db.refresh(order)

            order_items = order_item_repo.get_by_order(order.id)
            for item in order_items:
                supplier = item.supplier or select_supplier(db, item.product_id)
                if not supplier:
                    item.status = FAILED_STATUS
                    db.add(item)
                    continue

                item.supplier = supplier
                item.supplier_id = supplier.id
                item.status = PROCESSING_STATUS
                db.add(item)
                db.commit()
                db.refresh(item)

                tracking_number = adapter.place_order(order, item, supplier)
                item.tracking_number = tracking_number
                item.status = FULFILLED_STATUS
                db.add(item)

            if all(i.status == FULFILLED_STATUS for i in order_items):
                order.status = FULFILLED_STATUS
                order.tracking_number = order.tracking_number or next(
                    (i.tracking_number for i in order_items if i.tracking_number),
                    None,
                )
            elif any(i.status == FAILED_STATUS for i in order_items):
                order.status = FAILED_STATUS
            else:
                order.status = PENDING_STATUS

            db.add(order)
            db.commit()
            db.refresh(order)
            processed_orders.append(order)

            if order.status == FULFILLED_STATUS:
                collector.increment("orders.fulfilled", 1, store_id=order.store_id)
            elif order.status == FAILED_STATUS:
                collector.increment("orders.failed", 1, store_id=order.store_id)
    finally:
        if close_session:
            db.close()

    return processed_orders


def start_order_processing_scheduler(
    interval_minutes: int = 5,
    scheduler: Optional["BackgroundScheduler"] = None,
    store_id: Optional[int] = None,
) -> "BackgroundScheduler":
    """Start a scheduler that periodically processes pending orders.

    If ``store_id`` is provided, only orders from that store are processed.
    """

    if BackgroundScheduler is None:  # pragma: no cover - dependency guard
        raise ImportError("APScheduler is required to start the order scheduler.")

    scheduler = scheduler or BackgroundScheduler()
    job_id = "process_pending_orders" if store_id is None else f"process_pending_orders_{store_id}"
    scheduler.add_job(
        process_pending_orders,
        "interval",
        minutes=interval_minutes,
        kwargs={"store_id": store_id},
        id=job_id,
        replace_existing=True,
    )
    scheduler.start()
    LOGGER.info("Order processing scheduled every %s minutes", interval_minutes)
    return scheduler
