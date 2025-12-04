"""Entry point for Duplicate Site Creator."""
from __future__ import annotations

import argparse
from typing import Dict, Optional

from core.config.settings import get_timezone, load_config
from core.db.init_db import init_db
from core.dropship.order_processor import start_order_processing_scheduler
from core.inventory.sync_service import start_inventory_sync_scheduler
from core.logging.logger import get_logger
from core.store_manager import StoreManager


LOGGER = get_logger(__name__)


def bootstrap_application(
    env: str = "development",
    *,
    enable_schedulers: bool = True,
    launch_gui: bool = True,
    store_name: Optional[str] = None,
) -> Dict[str, object]:
    """Initialise core services, schedulers and (optionally) the GUI."""

    config = load_config()
    timezone = get_timezone()
    LOGGER.info("Starting Duplicate Site Creator in %s mode (tz=%s)", env, timezone)

    # Create tables before any controllers or schedulers run.
    init_db()
    LOGGER.info("Database initialised.")

    default_store_name = store_name or config.get("app", {}).get(
        "name", "Duplicate Site Creator"
    )
    store_manager = StoreManager()
    store = store_manager.ensure_store(default_store_name)
    store_id = store.id

    schedulers = {}
    if enable_schedulers:
        try:
            schedulers["orders"] = start_order_processing_scheduler()
            LOGGER.info("Order processing scheduler started.")
        except ImportError:
            LOGGER.warning(
                "APScheduler not installed; skipping order processing scheduler setup."
            )

        try:
            schedulers["inventory"] = start_inventory_sync_scheduler()
            LOGGER.info("Inventory sync scheduler started.")
        except ImportError:
            LOGGER.warning(
                "APScheduler not installed; skipping inventory sync scheduler setup."
            )

    if launch_gui:
        from app.gui import DuplicateSiteCreatorApp

        LOGGER.info("Launching GUI for store id %s", store_id)
        app = DuplicateSiteCreatorApp(store_id=store_id, store_manager=store_manager)
        try:
            app.mainloop()
        finally:
            for scheduler in schedulers.values():
                scheduler.shutdown(wait=False)
            LOGGER.info("Application closed; schedulers shut down.")

    return {"store_id": store_id, "store_manager": store_manager, "schedulers": schedulers}


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run Duplicate Site Creator")
    parser.add_argument(
        "--env",
        default="development",
        choices=["development", "production", "test"],
        help="Execution environment to use for logging and configuration",
    )
    parser.add_argument(
        "--no-gui", action="store_true", help="Start services without launching the GUI"
    )
    parser.add_argument(
        "--no-schedulers",
        action="store_true",
        help="Disable background schedulers (useful for testing)",
    )
    parser.add_argument(
        "--store-name",
        type=str,
        help="Optional store name to create or reuse for this session",
    )
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    bootstrap_application(
        args.env,
        enable_schedulers=not args.no_schedulers,
        launch_gui=not args.no_gui,
        store_name=args.store_name,
    )


if __name__ == "__main__":
    main()
