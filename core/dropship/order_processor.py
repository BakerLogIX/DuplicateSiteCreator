"""Process pending orders using the dummy adapter."""
from typing import Iterable

from sqlalchemy.orm import Session

from core.dropship.adapters.dummy_api import DummySupplierAdapter
from core.dropship.router import select_supplier
from core.logging.logger import get_logger
from core.models import Order, OrderItem

logger = get_logger(__name__)


def process_pending_orders(session: Session) -> Iterable[Order]:
    adapter = DummySupplierAdapter()
    orders = session.query(Order).filter(Order.status == "pending").all()
    for order in orders:
        supplier = order.supplier or select_supplier(session, order.id)
        if not supplier:
            logger.warning("No supplier found for order %s", order.id)
            continue
        for item in order.items:
            result = adapter.place_order(order, item, supplier)
            order.tracking_number = result.get("tracking")
            order.status = result.get("status", "pending")
        session.commit()
    return orders
