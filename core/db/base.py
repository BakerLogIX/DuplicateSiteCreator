"""Database base configuration and session management."""
from __future__ import annotations

from pathlib import Path
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, declarative_base, sessionmaker

from core.config.settings import get_db_url


def _ensure_sqlite_directory(url: str) -> None:
    """Ensure the directory for a SQLite database exists.

    Args:
        url: Database URL which may reference a SQLite file.
    """

    if url.startswith("sqlite"):
        # SQLite URL formats: sqlite:///relative/path.db or sqlite:////abs/path.db
        database_path = url.split("sqlite:///")[-1]
        if database_path:
            db_file = Path(database_path)
            if not db_file.is_absolute():
                db_file = Path.cwd() / db_file
            db_file.parent.mkdir(parents=True, exist_ok=True)


database_url = get_db_url()
_ensure_sqlite_directory(database_url)

engine = create_engine(
    database_url,
    connect_args={"check_same_thread": False} if database_url.startswith("sqlite") else {},
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """Provide a database session generator for dependency injection patterns."""

    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
