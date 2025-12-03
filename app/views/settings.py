"""Settings view exposing loaded configuration values."""
from __future__ import annotations

import tkinter as tk
from tkinter import ttk
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

        self.timezone_var = tk.StringVar(value=self.controller.get_timezone())
        ttk.Label(self, text="Timezone:").pack(anchor=tk.W, pady=(10, 0))
        ttk.Entry(self, textvariable=self.timezone_var, state="readonly", width=50).pack(
            anchor=tk.W
        )

        self.config_text = tk.Text(self, height=20, width=80)
        self.config_text.pack(fill=tk.BOTH, expand=True, pady=10)
        self._render_config()

    def _render_config(self) -> None:
        """Render the loaded YAML configuration for quick inspection."""

        config = self.controller.load_settings()
        self.config_text.delete("1.0", tk.END)
        for key, value in config.items():
            self.config_text.insert(tk.END, f"{key}: {value}\n")
        self.config_text.configure(state="disabled")


__all__ = ["SettingsView"]
