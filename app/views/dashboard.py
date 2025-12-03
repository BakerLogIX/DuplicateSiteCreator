"""Dashboard view displaying high-level metrics."""
from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Optional

from app.controllers.dashboard_controller import DashboardController, DashboardSummary


class DashboardView(ttk.Frame):
    """Simple dashboard surface showing key counts."""

    def __init__(
        self,
        parent: tk.Misc,
        *,
        controller: DashboardController,
        store_id: Optional[int] = None,
    ) -> None:
        super().__init__(parent, padding=20)
        self.controller = controller
        self.store_id = store_id

        self.header = ttk.Label(self, text="Dashboard", font=("TkDefaultFont", 16, "bold"))
        self.header.pack(anchor=tk.W)

        self.metrics = tk.StringVar(value="Loading metrics...")
        self.metrics_label = ttk.Label(self, textvariable=self.metrics, justify=tk.LEFT)
        self.metrics_label.pack(anchor=tk.W, pady=(10, 0))

    def render_summary(self, summary: DashboardSummary) -> None:
        """Update the metric labels with data from the controller."""

        metric_lines = [
            f"Products: {summary.product_count}",
            f"Pending orders: {summary.pending_orders}",
            f"Active suppliers: {summary.active_suppliers}",
        ]
        self.metrics.set("\n".join(metric_lines))


__all__ = ["DashboardView"]
