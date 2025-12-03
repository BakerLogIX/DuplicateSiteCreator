"""Dummy supplier adapter for testing and development."""
from __future__ import annotations

from datetime import datetime

from core.dropship.adapters.base import SupplierAdapter
from core.models.entities import Order, OrderItem, Supplier


class DummySupplierAdapter(SupplierAdapter):
    """Simulates supplier API interactions for testing purposes."""

    def place_order(self, order: Order, order_item: OrderItem, supplier: Supplier) -> str:
        timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
        return f"DUMMY-{supplier.id}-{order.id}-{order_item.id}-{timestamp}"

    def fetch_tracking(self, order: Order, supplier: Supplier) -> str | None:
        # For the dummy adapter, reuse the latest known tracking number if present.
        return order.tracking_number
