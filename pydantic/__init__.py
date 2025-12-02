"""Minimal pydantic BaseModel stub for offline environments."""
from __future__ import annotations

from typing import Any, Dict


class BaseModel:
    def __init__(self, **data: Any) -> None:
        for key, value in data.items():
            setattr(self, key, value)

    def dict(self) -> Dict[str, Any]:  # pragma: no cover - simple helper
        return dict(self.__dict__)

    class Config:
        orm_mode = True


__all__ = ["BaseModel"]
