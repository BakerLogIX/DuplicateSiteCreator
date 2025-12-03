"""Dashboard controller supplying aggregate metrics for the GUI."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from sqlalchemy.orm import Session

from core.db.base import SessionLocal
from core.db.repositories import OrderRepository, ProductRepository, SupplierRepository
from core.logging.logger import get_logger

LOGGER = get_logger(__name__)


@dataclass
class DashboardSummary:
    """Simple container for dashboard metrics."""

    product_count: int
    pending_orders: int
    active_suppliers: int


class DashboardController:
    """Provide quick summary metrics to display on the dashboard view."""

    def __init__(self, db: Optional[Session] = None) -> None:
        self.db = db or SessionLocal()

    def get_summary(self, store_id: Optional[int] = None) -> DashboardSummary:
        """Return a summary of key objects for the provided store."""

        product_repo = ProductRepository(self.db)
        order_repo = OrderRepository(self.db)
        supplier_repo = SupplierRepository(self.db)

        if store_id is None:
            product_count = len(product_repo.get_all())
            pending_orders = len(order_repo.get_pending_orders())
            active_suppliers = len(supplier_repo.get_active_suppliers())
        else:
            product_count = len(product_repo.get_by_store(store_id))
            pending_orders = len(order_repo.get_pending_orders(store_id=store_id))
            active_suppliers = len(supplier_repo.get_active_suppliers(store_id=store_id))

        summary = DashboardSummary(
            product_count=product_count,
            pending_orders=pending_orders,
            active_suppliers=active_suppliers,
        )
        LOGGER.info(
            "Dashboard summary for store %s: products=%s pending_orders=%s suppliers=%s",
            store_id,
            summary.product_count,
            summary.pending_orders,
            summary.active_suppliers,
        )
        return summary


__all__ = ["DashboardController", "DashboardSummary"]
