"""Dummy supplier adapter for testing."""
from core.dropship.adapters.base import SupplierAdapter
from core.models import Order, OrderItem, Supplier


class DummySupplierAdapter(SupplierAdapter):
    def place_order(self, order: Order, order_item: OrderItem, supplier: Supplier) -> dict:
        return {
            "order_id": order.id,
            "supplier": supplier.name,
            "status": "placed",
            "tracking": f"TRACK-{order.id}-{order_item.id}",
        }

    def fetch_tracking(self, order: Order, supplier: Supplier) -> str:
        return f"TRACK-{order.id}-{supplier.id}"
