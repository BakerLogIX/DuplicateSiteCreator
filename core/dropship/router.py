"""Supplier routing helpers."""
from __future__ import annotations

from typing import Optional

from sqlalchemy.orm import Session

from core.db.repositories import ProductRepository, SupplierRepository
from core.models.entities import Supplier


def select_supplier(db: Session, product_id: int) -> Optional[Supplier]:
    """Return the preferred supplier for a product.

    The current strategy selects the first active supplier for the store
    associated with the product. Future iterations can incorporate
    inventory checks, cost comparisons or routing rules.
    """

    product_repo = ProductRepository(db)
    supplier_repo = SupplierRepository(db)

    product = product_repo.get_by_id(product_id)
    if product is None:
        return None

    active_suppliers = supplier_repo.get_active_suppliers(product.store_id)
    if not active_suppliers:
        return None

    return active_suppliers[0]
