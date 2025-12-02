"""ORM submodule stubs mirroring a small subset of SQLAlchemy's API."""
from __future__ import annotations

from typing import Any, Type

from sqlalchemy import Column, create_engine, declarative_base, sessionmaker, Session


def relationship(_target: str, **_kwargs: Any) -> Any:  # pragma: no cover - descriptor placeholder
    return None


__all__ = [
    "Column",
    "Session",
    "create_engine",
    "declarative_base",
    "relationship",
    "sessionmaker",
]
