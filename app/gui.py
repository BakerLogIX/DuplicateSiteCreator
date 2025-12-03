"""Tkinter-based desktop GUI for Duplicate Site Creator.

This module wires together lightweight views and controllers to provide
navigation between scraping, pricing, inventory and order workflows.
"""
from __future__ import annotations

import threading
import tkinter as tk
from tkinter import ttk
from typing import Dict, Optional

from app.controllers.dashboard_controller import DashboardController
from app.controllers.orders_controller import OrdersController
from app.controllers.pricing_controller import PricingController
from app.controllers.products_controller import ProductsController
from app.controllers.scraper_controller import ScraperController
from app.controllers.settings_controller import SettingsController
from app.views.dashboard import DashboardView
from app.views.orders import OrdersView
from app.views.pricing import PricingView
from app.views.products import ProductsView
from app.views.scraper import ScraperView
from app.views.settings import SettingsView
from core.logging.logger import get_logger

LOGGER = get_logger(__name__)


class DuplicateSiteCreatorApp(tk.Tk):
    """Main application window with tabbed navigation."""

    def __init__(self, store_id: Optional[int] = None) -> None:
        super().__init__()
        self.title("Duplicate Site Creator")
        self.geometry("960x720")

        # Instantiate controllers shared across views.
        self.controllers: Dict[str, object] = {
            "dashboard": DashboardController(),
            "scraper": ScraperController(),
            "products": ProductsController(),
            "pricing": PricingController(),
            "orders": OrdersController(),
            "settings": SettingsController(),
        }
        self.store_id = store_id

        self._create_widgets()
        self._populate_dashboard()

    def _create_widgets(self) -> None:
        """Create the main notebook and register views."""

        notebook = ttk.Notebook(self)
        notebook.pack(fill=tk.BOTH, expand=True)

        # Dashboard
        self.dashboard_view = DashboardView(
            notebook, controller=self.controllers["dashboard"], store_id=self.store_id
        )
        notebook.add(self.dashboard_view, text="Dashboard")

        # Scraper
        self.scraper_view = ScraperView(
            notebook, controller=self.controllers["scraper"], store_id=self.store_id
        )
        notebook.add(self.scraper_view, text="Scraper")

        # Products
        self.products_view = ProductsView(
            notebook, controller=self.controllers["products"], store_id=self.store_id
        )
        notebook.add(self.products_view, text="Products")

        # Pricing
        self.pricing_view = PricingView(
            notebook, controller=self.controllers["pricing"], store_id=self.store_id
        )
        notebook.add(self.pricing_view, text="Pricing")

        # Orders
        self.orders_view = OrdersView(
            notebook, controller=self.controllers["orders"], store_id=self.store_id
        )
        notebook.add(self.orders_view, text="Orders")

        # Settings
        self.settings_view = SettingsView(
            notebook, controller=self.controllers["settings"], store_id=self.store_id
        )
        notebook.add(self.settings_view, text="Settings")

    def _populate_dashboard(self) -> None:
        """Refresh dashboard metrics asynchronously to keep UI responsive."""

        def load() -> None:
            try:
                summary = self.controllers["dashboard"].get_summary(store_id=self.store_id)
                self.dashboard_view.render_summary(summary)
            except Exception as exc:  # pragma: no cover - GUI fallback
                LOGGER.exception("Failed to load dashboard summary: %s", exc)

        threading.Thread(target=load, daemon=True).start()


__all__ = ["DuplicateSiteCreatorApp"]
