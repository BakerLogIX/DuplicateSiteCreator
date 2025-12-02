"""Base supplier adapter."""
from abc import ABC, abstractmethod
from typing import Any

from core.models import Order, OrderItem, Supplier


class SupplierAdapter(ABC):
    @abstractmethod
    def place_order(self, order: Order, order_item: OrderItem, supplier: Supplier) -> dict:
        raise NotImplementedError

    @abstractmethod
    def fetch_tracking(self, order: Order, supplier: Supplier) -> str:
        raise NotImplementedError
