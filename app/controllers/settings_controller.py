"""Controller that exposes configuration data for GUI settings screens."""
from __future__ import annotations

from typing import Any, Dict, Optional

from core.config import settings
from core.store_manager import StoreManager


class SettingsController:
    """Provide access to configuration and store-level settings for display/editing."""

    def __init__(self, store_manager: Optional[StoreManager] = None) -> None:
        self.store_manager = store_manager or StoreManager()

    def load_settings(self) -> Dict[str, Any]:
        """Return a snapshot of the loaded configuration."""

        return settings.load_config()

    def get_timezone(self) -> str:
        """Return the configured timezone."""

        return settings.get_timezone()

    def load_store_settings(self, store_id: Optional[int]) -> Optional[Dict[str, Any]]:
        """Return settings for a specific store, or None if it does not exist."""

        if store_id is None:
            return None
        store = self.store_manager.store_repo.get_by_id(store_id)
        if not store:
            return None
        return {
            "name": store.name,
            "theme": store.theme,
            "payment_provider": store.payment_provider or "",
            "default_currency": store.default_currency,
            "timezone": store.timezone,
        }

    def update_store_settings(self, store_id: int, **fields: Any) -> Dict[str, Any]:
        """Update store settings and return the new values."""

        updated = self.store_manager.update_store_settings(store_id, **fields)
        return {
            "name": updated.name,
            "theme": updated.theme,
            "payment_provider": updated.payment_provider or "",
            "default_currency": updated.default_currency,
            "timezone": updated.timezone,
        }


__all__ = ["SettingsController"]
