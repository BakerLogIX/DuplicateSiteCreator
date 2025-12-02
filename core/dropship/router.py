"""Supplier routing logic."""
from typing import Optional

from sqlalchemy.orm import Session

from core.models import Product, Supplier


def select_supplier(session: Session, product_id: int) -> Optional[Supplier]:
    # Naive routing: pick the first supplier
    supplier = session.query(Supplier).first()
    return supplier
