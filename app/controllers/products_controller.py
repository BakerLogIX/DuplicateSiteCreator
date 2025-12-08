"""Controller helpers for product listings in the GUI."""
from __future__ import annotations

from typing import List, Optional

from sqlalchemy.orm import Session

from core.db.base import SessionLocal
from core.db.repositories import ProductRepository
from core.models.entities import Product
from core.store_manager import StoreManager


class ProductsController:
    """Retrieve product data for display in the GUI."""

    def __init__(
        self, db: Optional[Session] = None, *, store_manager: Optional[StoreManager] = None
    ) -> None:
        self.db = db or (store_manager.db if store_manager else None) or SessionLocal()
        self.repo = ProductRepository(self.db)
        self.store_manager = store_manager or StoreManager(self.db)

    def list_products(self, store_id: Optional[int] = None) -> List[Product]:
        """Return products filtered by store, defaulting to the active store."""

        target_store_id = store_id if store_id is not None else self.store_manager.get_current_store_id()
        if target_store_id is None:
            return []
        return self.repo.get_by_store(target_store_id)


__all__ = ["ProductsController"]
