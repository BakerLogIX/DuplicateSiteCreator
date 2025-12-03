"""Scraper view with form inputs to start a crawl."""
from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Optional

from app.controllers.scraper_controller import ScraperController


class ScraperView(ttk.Frame):
    """Form to trigger scraping and display status messages."""

    def __init__(
        self,
        parent: tk.Misc,
        *,
        controller: ScraperController,
        store_id: Optional[int] = None,
    ) -> None:
        super().__init__(parent, padding=20)
        self.controller = controller
        self.store_id = store_id

        ttk.Label(self, text="Scraper", font=("TkDefaultFont", 14, "bold")).pack(anchor=tk.W)

        form_frame = ttk.Frame(self)
        form_frame.pack(fill=tk.X, pady=10)

        ttk.Label(form_frame, text="Start URL:").grid(row=0, column=0, sticky=tk.W)
        self.url_var = tk.StringVar()
        ttk.Entry(form_frame, textvariable=self.url_var, width=60).grid(
            row=0, column=1, padx=8, sticky=tk.W
        )
        ttk.Button(form_frame, text="Run Scraper", command=self._on_start).grid(
            row=0, column=2, padx=4
        )

        self.status_var = tk.StringVar(value="Enter a URL and start the scraper.")
        ttk.Label(self, textvariable=self.status_var, wraplength=720, justify=tk.LEFT).pack(
            anchor=tk.W
        )

    def _on_start(self) -> None:
        """Kick off scraping via the controller."""

        url = self.url_var.get().strip()
        if not url:
            self.status_var.set("Please enter a start URL.")
            return
        if self.store_id is None:
            self.status_var.set("A store ID is required to run the scraper.")
            return

        self.status_var.set("Scraping in progress...")

        def handle_complete(count: int) -> None:
            self.status_var.set(f"Scraping complete. {count} products discovered.")

        def handle_error(exc: Exception) -> None:  # pragma: no cover - GUI safety
            self.status_var.set(f"Scraper failed: {exc}")

        self.controller.scrape_async(
            url,
            store_id=self.store_id,
            on_complete=handle_complete,
            on_error=handle_error,
        )


__all__ = ["ScraperView"]
