"""Controller helpers for product listings in the GUI."""
from __future__ import annotations

from typing import List, Optional

from sqlalchemy.orm import Session

from core.db.base import SessionLocal
from core.db.repositories import ProductRepository
from core.models.entities import Product


class ProductsController:
    """Retrieve product data for display in the GUI."""

    def __init__(self, db: Optional[Session] = None) -> None:
        self.db = db or SessionLocal()
        self.repo = ProductRepository(self.db)

    def list_products(self, store_id: Optional[int] = None) -> List[Product]:
        """Return products filtered by store when provided."""

        if store_id is None:
            return self.repo.get_all()
        return self.repo.get_by_store(store_id)


__all__ = ["ProductsController"]
