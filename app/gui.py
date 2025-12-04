"""Tkinter-based desktop GUI for Duplicate Site Creator.

This module wires together lightweight views and controllers to provide
navigation between scraping, pricing, inventory and order workflows.
"""
from __future__ import annotations

import threading
import tkinter as tk
from tkinter import simpledialog, ttk
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
from core.store_manager import StoreManager

LOGGER = get_logger(__name__)


class DuplicateSiteCreatorApp(tk.Tk):
    """Main application window with tabbed navigation."""

    def __init__(
        self, store_id: Optional[int] = None, store_manager: Optional[StoreManager] = None
    ) -> None:
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
        self.store_manager = store_manager or StoreManager()
        self.store_id = store_id or self.store_manager.get_current_store_id()

        self._create_widgets()
        self._populate_dashboard()

    def _create_widgets(self) -> None:
        """Create the main notebook and register views."""

        selector_frame = ttk.Frame(self, padding=(10, 6))
        selector_frame.pack(fill=tk.X)
        ttk.Label(selector_frame, text="Active store:").pack(side=tk.LEFT)
        self.store_var = tk.StringVar(value="")
        self.store_selector = ttk.Combobox(
            selector_frame, textvariable=self.store_var, state="readonly", width=40
        )
        self.store_selector.pack(side=tk.LEFT, padx=(6, 6))
        self.store_selector.bind("<<ComboboxSelected>>", self._on_store_selected)
        ttk.Button(
            selector_frame, text="New store", command=self._prompt_create_store
        ).pack(side=tk.LEFT)

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

        self._refresh_store_selector()

    def _populate_dashboard(self) -> None:
        """Refresh dashboard metrics asynchronously to keep UI responsive."""

        def load() -> None:
            try:
                self.dashboard_view.refresh(store_id=self.store_id)
            except Exception as exc:  # pragma: no cover - GUI fallback
                LOGGER.exception("Failed to load dashboard summary: %s", exc)

        threading.Thread(target=load, daemon=True).start()

    def _on_store_selected(self, event: tk.Event) -> None:  # pragma: no cover - GUI wiring
        """Handle user selection from the store dropdown."""

        selection = self.store_var.get()
        if not selection:
            return
        store_id = self._store_name_to_id.get(selection)
        if store_id is None:
            return
        self._set_store(store_id)

    def _prompt_create_store(self) -> None:  # pragma: no cover - GUI wiring
        """Display a prompt to create a new store and refresh the selector."""

        name = simpledialog.askstring("Create store", "Store name:", parent=self)
        if not name:
            return
        store = self.store_manager.create_store(name=name)
        self._refresh_store_selector(select_id=store.id)
        self._set_store(store.id)

    def _refresh_store_selector(self, select_id: Optional[int] = None) -> None:
        """Reload available stores into the dropdown and update selection."""

        stores = self.store_manager.list_stores()
        self._store_name_to_id = {f"{store.name} (#{store.id})": store.id for store in stores}
        names = list(self._store_name_to_id.keys())
        self.store_selector.configure(values=names)

        target_id = select_id or self.store_id or self.store_manager.get_current_store_id()
        active_name = None
        for name, sid in self._store_name_to_id.items():
            if sid == target_id:
                active_name = name
                break
        if active_name:
            self.store_var.set(active_name)
            self.store_id = target_id

    def _set_store(self, store_id: int) -> None:
        """Switch the active store and refresh relevant views."""

        try:
            self.store_manager.set_current_store(store_id)
        except ValueError:
            LOGGER.warning("Requested store id %s does not exist", store_id)
            return

        self.store_id = store_id
        self.dashboard_view.refresh(store_id)
        self.products_view.set_store(store_id)
        self.orders_view.set_store(store_id)
        self.scraper_view.set_store(store_id)
        self.pricing_view.set_store(store_id)


__all__ = ["DuplicateSiteCreatorApp"]
