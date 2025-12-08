"""Settings view exposing loaded configuration values."""
from __future__ import annotations

import tkinter as tk
from tkinter import messagebox, ttk
from typing import Optional

from app.controllers.settings_controller import SettingsController


class SettingsView(ttk.Frame):
    """Display configuration in a read-only form."""

    def __init__(
        self,
        parent: tk.Misc,
        *,
        controller: SettingsController,
        store_id: Optional[int] = None,
    ) -> None:
        super().__init__(parent, padding=20)
        self.controller = controller
        self.store_id = store_id

        ttk.Label(self, text="Settings", font=("TkDefaultFont", 14, "bold")).pack(anchor=tk.W)

        self.store_name_var = tk.StringVar(value="")
        self.theme_var = tk.StringVar(value="")
        self.payment_provider_var = tk.StringVar(value="")
        self.currency_var = tk.StringVar(value="")
        self.timezone_var = tk.StringVar(value=self.controller.get_timezone())
        self.status_var = tk.StringVar(value="")

        store_frame = ttk.LabelFrame(self, text="Store settings", padding=12)
        store_frame.pack(fill=tk.X, pady=(10, 10))

        self._add_labeled_entry(store_frame, "Store name:", self.store_name_var)
        self._add_labeled_entry(store_frame, "Theme:", self.theme_var)
        self._add_labeled_entry(store_frame, "Payment provider:", self.payment_provider_var)
        self._add_labeled_entry(store_frame, "Default currency:", self.currency_var)
        self._add_labeled_entry(store_frame, "Timezone:", self.timezone_var)

        ttk.Button(store_frame, text="Save store settings", command=self._save_store_settings).pack(
            anchor=tk.E, pady=(6, 0)
        )
        ttk.Label(store_frame, textvariable=self.status_var, foreground="green").pack(
            anchor=tk.W, pady=(2, 0)
        )

        self.config_text = tk.Text(self, height=20, width=80)
        self.config_text.pack(fill=tk.BOTH, expand=True, pady=10)
        self._render_config()
        self._load_store_settings()

    def _add_labeled_entry(self, parent: tk.Misc, label: str, variable: tk.StringVar) -> None:
        """Helper to create a labeled entry bound to a variable."""

        row = ttk.Frame(parent)
        row.pack(fill=tk.X, pady=2)
        ttk.Label(row, text=label, width=18).pack(side=tk.LEFT)
        ttk.Entry(row, textvariable=variable, width=40).pack(side=tk.LEFT, fill=tk.X, expand=True)

    def _render_config(self) -> None:
        """Render the loaded YAML configuration for quick inspection."""

        config = self.controller.load_settings()
        self.config_text.delete("1.0", tk.END)
        for key, value in config.items():
            self.config_text.insert(tk.END, f"{key}: {value}\n")
        self.config_text.configure(state="disabled")

    def _load_store_settings(self) -> None:
        """Populate the store-specific settings fields."""

        store_settings = self.controller.load_store_settings(self.store_id)
        if not store_settings:
            self.status_var.set("No store selected.")
            return

        self.store_name_var.set(store_settings["name"])
        self.theme_var.set(store_settings["theme"])
        self.payment_provider_var.set(store_settings["payment_provider"])
        self.currency_var.set(store_settings["default_currency"])
        self.timezone_var.set(store_settings["timezone"])
        self.status_var.set("")

    def _save_store_settings(self) -> None:
        """Persist store settings changes."""

        if self.store_id is None:
            messagebox.showwarning("Store settings", "No store selected.")
            return

        updated = self.controller.update_store_settings(
            self.store_id,
            name=self.store_name_var.get().strip(),
            theme=self.theme_var.get().strip() or "default",
            payment_provider=self.payment_provider_var.get().strip() or None,
            default_currency=self.currency_var.get().strip() or "USD",
            timezone=self.timezone_var.get().strip() or "UTC",
        )
        self.status_var.set("Saved store settings.")
        self.store_name_var.set(updated["name"])
        self.theme_var.set(updated["theme"])
        self.payment_provider_var.set(updated["payment_provider"])
        self.currency_var.set(updated["default_currency"])
        self.timezone_var.set(updated["timezone"])

    def set_store(self, store_id: Optional[int]) -> None:
        """Update the view to reflect the provided store."""

        self.store_id = store_id
        self._load_store_settings()


__all__ = ["SettingsView"]
