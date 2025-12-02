"""Database initialization helpers."""
from core.db.base import Base, engine
import core.models  # noqa: F401 - ensure models are imported for metadata registration


def init_db() -> None:
    """Create database tables based on SQLAlchemy metadata."""
    Base.metadata.create_all(bind=engine)
