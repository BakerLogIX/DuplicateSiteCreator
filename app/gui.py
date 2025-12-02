"""Placeholder GUI entry point."""

from core.logging.logger import get_logger

logger = get_logger(__name__)


def launch_app() -> None:
    logger.info("Launching DuplicateSiteCreator GUI (placeholder).")


if __name__ == "__main__":
    launch_app()
