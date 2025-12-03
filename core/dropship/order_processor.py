"""Order processing and scheduling utilities."""
from __future__ import annotations

from typing import List, Optional

from core.db.base import SessionLocal
from core.db.repositories import OrderItemRepository, OrderRepository
from core.dropship.adapters import DummySupplierAdapter, SupplierAdapter
from core.dropship.router import select_supplier
from core.logging.logger import get_logger
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
    db=None, adapter: Optional[SupplierAdapter] = None
) -> List[Order]:
    """Process pending orders by routing items to suppliers.

    Args:
        db: Optional SQLAlchemy session. If omitted, a new session is created.
        adapter: Supplier adapter used to communicate with suppliers. Defaults
            to the :class:`DummySupplierAdapter`.

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
    processed_orders = []

    try:
        pending_orders = order_repo.get_pending_orders()
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
    finally:
        if close_session:
            db.close()

    return processed_orders


def start_order_processing_scheduler(
    interval_minutes: int = 5, scheduler: Optional["BackgroundScheduler"] = None
) -> "BackgroundScheduler":
    """Start a scheduler that periodically processes pending orders."""

    if BackgroundScheduler is None:  # pragma: no cover - dependency guard
        raise ImportError("APScheduler is required to start the order scheduler.")

    scheduler = scheduler or BackgroundScheduler()
    scheduler.add_job(
        process_pending_orders,
        "interval",
        minutes=interval_minutes,
        id="process_pending_orders",
        replace_existing=True,
    )
    scheduler.start()
    LOGGER.info("Order processing scheduled every %s minutes", interval_minutes)
    return scheduler
