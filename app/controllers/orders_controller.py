"""Controller utilities for managing orders in the GUI."""
from __future__ import annotations

from typing import List, Optional

from sqlalchemy.orm import Session

from core.db.base import SessionLocal
from core.db.repositories import OrderRepository
from core.models.entities import Order


class OrdersController:
    """Provide order listing helpers for the orders view."""

    def __init__(self, db: Optional[Session] = None) -> None:
        self.db = db or SessionLocal()
        self.repo = OrderRepository(self.db)

    def list_orders(self, store_id: Optional[int] = None) -> List[Order]:
        """Return orders for the given store or all stores when omitted."""

        if store_id is None:
            return self.repo.get_all()
        return self.repo.get_by_store(store_id)

    def list_pending(self, store_id: Optional[int] = None) -> List[Order]:
        """Return orders still marked as pending."""

        return self.repo.get_pending_orders(store_id=store_id)


__all__ = ["OrdersController"]
