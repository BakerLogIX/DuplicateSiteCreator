"""Application entry point for DuplicateSiteCreator."""
from core.db.init_db import init_db
from core.logging.logger import get_logger

logger = get_logger(__name__)


def bootstrap() -> None:
    """Initialize services and prepare the application."""
    logger.info("Initialising database...")
    init_db()
    logger.info("Startup complete.")


if __name__ == "__main__":
    bootstrap()
