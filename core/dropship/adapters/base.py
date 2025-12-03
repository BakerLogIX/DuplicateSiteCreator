"""Abstract supplier adapter interface."""
from __future__ import annotations

from abc import ABC, abstractmethod

from core.models.entities import Order, OrderItem, Supplier


class SupplierAdapter(ABC):
    """Adapter interface for interacting with supplier systems."""

    @abstractmethod
    def place_order(self, order: Order, order_item: OrderItem, supplier: Supplier) -> str:
        """Place an order for a specific item with the supplier.

        Args:
            order: The order containing the item.
            order_item: The item to fulfil.
            supplier: The supplier that will fulfil the item.

        Returns:
            A tracking number reference provided by the supplier.
        """

    @abstractmethod
    def fetch_tracking(self, order: Order, supplier: Supplier) -> str | None:
        """Fetch the latest tracking number for an order from the supplier."""
