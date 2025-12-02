"""Logging helpers for the DuplicateSiteCreator project."""
import logging
from typing import Optional

from core.config import settings


def get_logger(name: str, level: Optional[str | int] = None) -> logging.Logger:
    """Return a configured logger with a console handler."""
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter(settings.get_log_format())
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    logger.setLevel(level or settings.get_log_level())
    logger.propagate = False
    return logger
