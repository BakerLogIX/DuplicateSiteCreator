"""Minimal Pydantic stubs used for offline testing."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict


@dataclass
class ConfigDict:
    from_attributes: bool = False


class BaseModel:
    def __init__(self, **data: Any) -> None:
        for key, value in data.items():
            setattr(self, key, value)

    def model_dump(self) -> Dict[str, Any]:  # pragma: no cover - helper for compatibility
        return self.__dict__.copy()

    class Config:
        orm_mode = True


__all__ = ["BaseModel", "ConfigDict"]
