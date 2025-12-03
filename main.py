"""Entry point for Duplicate Site Creator."""
from __future__ import annotations

from core.db.init_db import init_db
from core.dropship.order_processor import start_order_processing_scheduler
from core.inventory.sync_service import start_inventory_sync_scheduler
from core.logging.logger import get_logger


LOGGER = get_logger(__name__)


def main() -> None:
    """Bootstrap the application by initialising the database."""

    init_db()
    LOGGER.info("Database initialised.")

    try:
        start_order_processing_scheduler()
        LOGGER.info("Order processing scheduler started.")
    except ImportError:
        LOGGER.warning(
            "APScheduler not installed; skipping order processing scheduler setup."
        )

    try:
        start_inventory_sync_scheduler()
        LOGGER.info("Inventory sync scheduler started.")
    except ImportError:
        LOGGER.warning(
            "APScheduler not installed; skipping inventory sync scheduler setup."
        )


if __name__ == "__main__":
    main()
