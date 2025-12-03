"""Controller that exposes configuration data for GUI settings screens."""
from __future__ import annotations

from typing import Any, Dict

from core.config import settings


class SettingsController:
    """Provide read-only access to configuration values for display."""

    def load_settings(self) -> Dict[str, Any]:
        """Return a snapshot of the loaded configuration."""

        return settings.load_config()

    def get_timezone(self) -> str:
        """Return the configured timezone."""

        return settings.get_timezone()


__all__ = ["SettingsController"]
