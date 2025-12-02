"""Entry point for Duplicate Site Creator."""
from __future__ import annotations

from core.db.init_db import init_db
from core.logging.logger import get_logger


LOGGER = get_logger(__name__)


def main() -> None:
    """Bootstrap the application by initialising the database."""

    init_db()
    LOGGER.info("Database initialised.")


if __name__ == "__main__":
    main()
