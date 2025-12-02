"""Logging helper wrapping Python's standard logging module."""
from __future__ import annotations

import logging
from typing import Optional

from core.config.settings import get_logging_settings


_CONFIGURED = False


def _configure_logging() -> None:
    """Configure the root logger using settings from the configuration file."""

    global _CONFIGURED
    settings = get_logging_settings()
    level_name = str(settings.get("level", "INFO")).upper()
    level = getattr(logging, level_name, logging.INFO)

    logging.basicConfig(
        level=level,
        format=settings.get("format"),
        datefmt=settings.get("datefmt"),
    )
    _CONFIGURED = True


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """Return a configured logger instance.

    Args:
        name: Optional logger name. Defaults to the root logger when ``None``.

    Returns:
        A :class:`logging.Logger` configured according to ``config.yaml``.
    """

    if not _CONFIGURED:
        _configure_logging()

    logger = logging.getLogger(name)
    # Ensure the logger respects the configured level even if created after
    # configuration.
    settings = get_logging_settings()
    level_name = str(settings.get("level", "INFO")).upper()
    logger.setLevel(getattr(logging, level_name, logging.INFO))
    return logger
