"""Lightweight pricing view helpers for GUI integration."""
from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Iterable, Optional

from app.controllers.pricing_controller import PricingController
from core.models.entities import Product


def pricing_summary(products: Iterable[Product]) -> str:
    """Return a human-readable summary of pricing results for display in the UI."""

    product_list = list(products)
    if not product_list:
        return "No products were updated during pricing."

    lines = ["Updated product prices:"]
    for product in product_list:
        lines.append(f"- {product.name}: {product.price} {product.currency}")
    return "\n".join(lines)


class PricingView(ttk.Frame):
    """Run pricing and display results."""

    def __init__(
        self,
        parent: tk.Misc,
        *,
        controller: PricingController,
        store_id: Optional[int] = None,
    ) -> None:
        super().__init__(parent, padding=20)
        self.controller = controller
        self.store_id = store_id

        ttk.Label(self, text="Pricing", font=("TkDefaultFont", 14, "bold")).pack(anchor=tk.W)

        ttk.Button(self, text="Run Pricing", command=self._on_run).pack(anchor=tk.W, pady=10)

        self.output = tk.Text(self, height=20, width=90)
        self.output.pack(fill=tk.BOTH, expand=True)
        self.output.insert(tk.END, "Click 'Run Pricing' to calculate updated prices.\n")

    def _on_run(self) -> None:
        """Trigger pricing via the controller and display a summary."""

        if self.store_id is None:
            self._set_output("A store ID is required to run pricing.")
            return

        updated_products = self.controller.run_pricing(store_id=self.store_id)
        self._set_output(pricing_summary(updated_products))

    def set_store(self, store_id: Optional[int]) -> None:
        """Change the active store used when running pricing."""

        self.store_id = store_id
        self._set_output("Store changed. Click 'Run Pricing' to recalculate prices.")

    def _set_output(self, text: str) -> None:
        self.output.configure(state="normal")
        self.output.delete("1.0", tk.END)
        self.output.insert(tk.END, text)
        self.output.configure(state="disabled")


__all__ = ["pricing_summary", "PricingView"]
