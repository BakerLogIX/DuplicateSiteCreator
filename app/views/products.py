"""Product list view for the GUI."""
from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Optional

from app.controllers.products_controller import ProductsController


class ProductsView(ttk.Frame):
    """Display products in a tree view."""

    def __init__(
        self,
        parent: tk.Misc,
        *,
        controller: ProductsController,
        store_id: Optional[int] = None,
    ) -> None:
        super().__init__(parent, padding=20)
        self.controller = controller
        self.store_id = store_id

        ttk.Label(self, text="Products", font=("TkDefaultFont", 14, "bold")).pack(anchor=tk.W)

        columns = ("Name", "SKU", "Price", "Currency")
        self.tree = ttk.Treeview(self, columns=columns, show="headings", height=18)
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, anchor=tk.W, width=200)
        self.tree.pack(fill=tk.BOTH, expand=True, pady=(10, 0))

        ttk.Button(self, text="Refresh", command=self.refresh).pack(anchor=tk.E, pady=10)
        self.refresh()

    def refresh(self) -> None:
        """Reload product data from the controller."""

        for item in self.tree.get_children():
            self.tree.delete(item)

        products = self.controller.list_products(store_id=self.store_id)
        for product in products:
            self.tree.insert(
                "", tk.END, values=(product.name, product.sku, product.price, product.currency)
            )

    def set_store(self, store_id: Optional[int]) -> None:
        """Update the active store and refresh the listing."""

        self.store_id = store_id
        self.refresh()


__all__ = ["ProductsView"]
