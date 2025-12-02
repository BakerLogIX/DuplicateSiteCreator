"""Database initialisation helper."""
from __future__ import annotations

from core.db.base import Base, engine
from core import models  # noqa: F401 - imported for side effects


def init_db() -> None:
    """Create all database tables defined by the SQLAlchemy models."""

    Base.metadata.create_all(bind=engine)
