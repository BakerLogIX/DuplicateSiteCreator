"""Dashboard controller supplying aggregate metrics for the GUI."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Optional

from sqlalchemy.orm import Session

from core.db.base import SessionLocal
from core.db.repositories import OrderRepository, ProductRepository, SupplierRepository
from core.logging.logger import get_logger
from core.metrics import get_collector
from core.store_manager import StoreManager

LOGGER = get_logger(__name__)


@dataclass
class DashboardSummary:
    """Simple container for dashboard metrics."""

    product_count: int
    pending_orders: int
    active_suppliers: int
    metrics: Dict[str, Any] = field(default_factory=dict)


class DashboardController:
    """Provide quick summary metrics to display on the dashboard view."""

    def __init__(
        self, db: Optional[Session] = None, *, store_manager: Optional[StoreManager] = None
    ) -> None:
        self.db = db or (store_manager.db if store_manager else None) or SessionLocal()
        self.store_manager = store_manager or StoreManager(self.db)

    def get_summary(self, store_id: Optional[int] = None) -> DashboardSummary:
        """Return a summary of key objects for the provided store."""

        product_repo = ProductRepository(self.db)
        order_repo = OrderRepository(self.db)
        supplier_repo = SupplierRepository(self.db)
        collector = get_collector()

        target_store_id = store_id if store_id is not None else self.store_manager.get_current_store_id()
        if target_store_id is None:
            product_count = 0
            pending_orders = 0
            active_suppliers = 0
            metrics = {}
        else:
            product_count = len(product_repo.get_by_store(target_store_id))
            pending_orders = len(order_repo.get_pending_orders(store_id=target_store_id))
            active_suppliers = len(supplier_repo.get_active_suppliers(store_id=target_store_id))
            snapshot = collector.get_snapshot(target_store_id)
            pricing_stats = snapshot["measurements"].get("pricing.uplift_total")
            metrics = {
                "products_scraped": int(snapshot["counters"].get("scraper.products_discovered", 0)),
                "pages_generated": int(snapshot["counters"].get("storegen.pages_generated", 0)),
                "orders_fulfilled": int(snapshot["counters"].get("orders.fulfilled", 0)),
                "pricing_uplift": round(pricing_stats.avg, 2) if pricing_stats else 0,
            }

        summary = DashboardSummary(
            product_count=product_count,
            pending_orders=pending_orders,
            active_suppliers=active_suppliers,
            metrics=metrics,
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
