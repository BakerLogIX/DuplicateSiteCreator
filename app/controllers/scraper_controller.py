"""Controller helpers to initiate scraping workflows from the GUI."""
from __future__ import annotations

import threading
from typing import Callable, Optional

from sqlalchemy.orm import Session

from core.logging.logger import get_logger
from core.scraper.orchestrator import run_scrape

LOGGER = get_logger(__name__)


class ScraperController:
    """Wrap scraper orchestration with optional callbacks for progress."""

    def __init__(self, db: Optional[Session] = None) -> None:
        self.db = db

    def scrape_async(
        self,
        start_url: str,
        store_id: int,
        on_complete: Optional[Callable[[int], None]] = None,
        on_error: Optional[Callable[[Exception], None]] = None,
    ) -> threading.Thread:
        """Run the scraper in a background thread.

        Args:
            start_url: URL to begin crawling from.
            store_id: Store context for the crawl.
            on_complete: Optional callback receiving the number of products scraped.
            on_error: Optional callback receiving an exception raised during scrape.
        """

        def _target() -> None:
            try:
                LOGGER.info("Starting scrape for %s", start_url)
                results = run_scrape(start_url=start_url, store_id=store_id, db=self.db)
                LOGGER.info("Scrape completed for %s; %d products discovered", start_url, len(results))
                if on_complete:
                    on_complete(len(results))
            except Exception as exc:  # pragma: no cover - runtime guard for GUI
                LOGGER.exception("Scrape failed for %s", start_url)
                if on_error:
                    on_error(exc)

        thread = threading.Thread(target=_target, daemon=True)
        thread.start()
        return thread


__all__ = ["ScraperController"]
