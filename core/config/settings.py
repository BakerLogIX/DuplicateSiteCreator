"""Configuration utilities for the DuplicateSiteCreator project."""
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict

import yaml


CONFIG_PATH = Path(__file__).resolve().parents[2] / "config.yaml"


def _load_yaml_config(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}

    with path.open("r", encoding="utf-8") as config_file:
        return yaml.safe_load(config_file) or {}


@lru_cache(maxsize=1)
def get_settings() -> Dict[str, Any]:
    """Load the YAML configuration once and cache the result."""
    return _load_yaml_config(CONFIG_PATH)


def get_db_url() -> str:
    settings = get_settings()
    return settings.get("database", {}).get("url", "sqlite:///./duplicate_site.db")


def get_default_currency() -> str:
    settings = get_settings()
    return settings.get("pricing", {}).get("default_currency", "USD")


def get_default_margin() -> float:
    settings = get_settings()
    return float(settings.get("pricing", {}).get("default_margin", 0.0))


def get_log_config() -> Dict[str, Any]:
    settings = get_settings()
    return settings.get("logging", {})


def get_log_level() -> str:
    return get_log_config().get("level", "INFO")


def get_log_format() -> str:
    return get_log_config().get(
        "format", "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    )
