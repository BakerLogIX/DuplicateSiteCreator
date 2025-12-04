"""Application configuration loader.

This module reads settings from ``config.yaml`` located at the project root
and exposes helper functions for commonly used configuration values.
"""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any, Dict

import yaml

CONFIG_FILENAME = "config.yaml"


def _config_path() -> Path:
    """Return the absolute path to the configuration file.

    The configuration file is expected to live at the repository root. This
    function resolves the path relative to this module so that it works
    regardless of the current working directory.
    """

    return Path(__file__).resolve().parents[2] / CONFIG_FILENAME


@lru_cache(maxsize=1)
def load_config() -> Dict[str, Any]:
    """Load and cache configuration values from ``config.yaml``.

    Returns:
        A dictionary of configuration values parsed from YAML.

    Raises:
        FileNotFoundError: If the configuration file cannot be located.
        yaml.YAMLError: If the configuration file contains invalid YAML.
    """

    config_file = _config_path()
    if not config_file.exists():
        raise FileNotFoundError(f"Configuration file not found at {config_file}")

    with config_file.open("r", encoding="utf-8") as fh:
        return yaml.safe_load(fh) or {}


def get_db_url() -> str:
    """Return the database URL defined in the configuration.

    Returns:
        The database URL string.

    Raises:
        KeyError: If the database URL is missing from the configuration.
    """

    config = load_config()
    try:
        return config["database"]["url"]
    except KeyError as exc:  # pragma: no cover - defensive path
        raise KeyError("Database URL not configured in config.yaml") from exc


def get_default_currency() -> str:
    """Return the application's default currency code.

    Falls back to ``USD`` if the configuration is missing this value.
    """

    config = load_config()
    return config.get("app", {}).get("default_currency", "USD")


def get_logging_settings() -> Dict[str, Any]:
    """Return logging-related configuration values.

    Provides sensible defaults if values are missing.
    """

    defaults = {
        "level": "INFO",
        "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        "datefmt": "%Y-%m-%d %H:%M:%S",
    }
    config = load_config()
    logging_config = config.get("logging", {})
    return {**defaults, **logging_config}


def get_timezone() -> str:
    """Return the configured timezone string, defaulting to UTC."""

    config = load_config()
    return config.get("app", {}).get("timezone", "UTC")


def get_payments_config() -> Dict[str, Any]:
    """Return payment configuration settings."""

    config = load_config()
    return config.get("payments", {})
