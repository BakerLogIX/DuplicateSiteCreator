"""Service helpers for creating and selecting stores."""
from __future__ import annotations

from typing import List, Optional

from sqlalchemy.orm import Session

from core.db.base import SessionLocal
from core.db.repositories import StoreRepository
from core.logging.logger import get_logger
from core.models.entities import Store

LOGGER = get_logger(__name__)


class StoreManager:
    """Manage store lifecycle and selection for multi-store setups."""

    def __init__(self, db: Optional[Session] = None) -> None:
        self.db = db or SessionLocal()
        self.store_repo = StoreRepository(self.db)
        self._current_store_id: Optional[int] = None

    def list_stores(self) -> List[Store]:
        """Return all stores sorted by creation order."""

        return self.store_repo.get_all()

    def create_store(
        self,
        *,
        name: str,
        theme: str = "default",
        payment_provider: Optional[str] = None,
        default_currency: str = "USD",
        timezone: str = "UTC",
    ) -> Store:
        """Create a new store and select it as current."""

        store = self.store_repo.create(
            name=name,
            theme=theme,
            payment_provider=payment_provider,
            default_currency=default_currency,
            timezone=timezone,
        )
        self._current_store_id = store.id
        LOGGER.info("Created store '%s' (id=%s)", store.name, store.id)
        return store

    def ensure_store(
        self,
        name: str,
        *,
        theme: str = "default",
        payment_provider: Optional[str] = None,
        default_currency: str = "USD",
        timezone: str = "UTC",
    ) -> Store:
        """Return an existing store by name or create it if missing."""

        existing = self.store_repo.get_by_name(name)
        if existing:
            if self._current_store_id is None:
                self._current_store_id = existing.id
            return existing

        return self.create_store(
            name=name,
            theme=theme,
            payment_provider=payment_provider,
            default_currency=default_currency,
            timezone=timezone,
        )

    def set_current_store(self, store_id: int) -> Store:
        """Set the active store by ID after validating it exists."""

        store = self.store_repo.get_by_id(store_id)
        if not store:
            raise ValueError(f"Store with id {store_id} not found")

        self._current_store_id = store.id
        return store

    def get_current_store_id(self) -> Optional[int]:
        """Return the current store ID, defaulting to the first store if unset."""

        if self._current_store_id is not None:
            return self._current_store_id

        stores = self.list_stores()
        if stores:
            self._current_store_id = stores[0].id
            return self._current_store_id

        return None

    def get_current_store(self) -> Optional[Store]:
        """Return the currently selected store instance."""

        store_id = self.get_current_store_id()
        if store_id is None:
            return None
        return self.store_repo.get_by_id(store_id)


__all__ = ["StoreManager"]
