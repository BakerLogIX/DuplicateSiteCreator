from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict


@dataclass
class ConfigDict:
    """Lightweight stand-in for Pydantic's ConfigDict.

    The implementation only stores the provided keyword arguments so schemas can
    declare ``model_config = ConfigDict(...)`` without pulling the real
    dependency in offline environments.
    """

    from_attributes: bool = False


class BaseModel:
    """Minimal BaseModel that mirrors attribute assignment semantics."""

    model_config: ConfigDict | None = None

    def __init__(self, **data: Any) -> None:
        for key, value in data.items():
            setattr(self, key, value)

    def dict(self) -> Dict[str, Any]:
        """Return a shallow dict of the stored attributes."""

        return dict(self.__dict__)

    # Pydantic v2 compatibility helper
    def model_dump(self) -> Dict[str, Any]:  # pragma: no cover - convenience
        return self.dict()


__all__ = ["BaseModel", "ConfigDict"]
