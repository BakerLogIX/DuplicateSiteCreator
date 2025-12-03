"""Orders view rendering basic order information."""
from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Optional

from app.controllers.orders_controller import OrdersController


class OrdersView(ttk.Frame):
    """List orders and highlight pending items."""

    def __init__(
        self,
        parent: tk.Misc,
        *,
        controller: OrdersController,
        store_id: Optional[int] = None,
    ) -> None:
        super().__init__(parent, padding=20)
        self.controller = controller
        self.store_id = store_id

        ttk.Label(self, text="Orders", font=("TkDefaultFont", 14, "bold")).pack(anchor=tk.W)

        columns = ("ID", "Status", "Customer", "Total")
        self.tree = ttk.Treeview(self, columns=columns, show="headings", height=16)
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, anchor=tk.W, width=180)
        self.tree.pack(fill=tk.BOTH, expand=True, pady=(10, 0))

        footer = ttk.Frame(self)
        footer.pack(fill=tk.X, pady=10)
        ttk.Button(footer, text="Refresh", command=self.refresh).pack(side=tk.RIGHT)

        self.refresh()

    def refresh(self) -> None:
        """Reload orders from the controller."""

        for item in self.tree.get_children():
            self.tree.delete(item)

        orders = self.controller.list_orders(store_id=self.store_id)
        for order in orders:
            self.tree.insert(
                "",
                tk.END,
                values=(order.id, order.status, getattr(order, "customer_email", ""), order.total),
            )


__all__ = ["OrdersView"]
