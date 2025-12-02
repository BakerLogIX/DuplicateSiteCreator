"""Lightweight SQLAlchemy-compatible stubs for offline testing.

This is a minimal subset of SQLAlchemy's API sufficient for the unit tests
in this repository. It should not be considered a drop-in replacement for the
real library.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any, Callable, Dict, List, Optional, Type


class _Type:
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        self.args = args
        self.kwargs = kwargs


class Integer(_Type):
    pass


class String(_Type):
    pass


class Numeric(_Type):
    pass


class Boolean(_Type):
    pass


class Text(_Type):
    pass


class DateTime(_Type):
    pass


class ForeignKey:
    def __init__(self, target: str) -> None:
        self.target = target


class Column:
    def __init__(
        self,
        _type: _Type,
        *args: Any,
        primary_key: bool = False,
        nullable: bool = True,
        default: Any = None,
        index: bool = False,
        unique: bool = False,
        **_: Any,
    ) -> None:
        self.type = _type
        self.foreign_key = next((arg for arg in args if isinstance(arg, ForeignKey)), None)
        self.primary_key = bool(primary_key)
        self.nullable = nullable
        self.default = default
        self.index = index
        self.unique = unique
        self.name: Optional[str] = None

    def __set_name__(self, owner: Type[Any], name: str) -> None:
        self.name = name
        if not hasattr(owner, "__columns__"):
            owner.__columns__ = {}
        owner.__columns__[name] = self
        if self.primary_key:
            owner.__primary_key__ = name

    def _value(self, instance: Any) -> Any:
        if self.name is None:
            return None
        if self.name in instance.__dict__:
            return instance.__dict__[self.name]
        if callable(self.default):
            return self.default()
        return self.default

    def __get__(self, instance: Any, owner: Type[Any]) -> Any:
        if instance is None:
            return self
        return self._value(instance)

    def __set__(self, instance: Any, value: Any) -> None:
        if self.name:
            instance.__dict__[self.name] = value


class Metadata:
    def __init__(self) -> None:
        self.tables: Dict[str, Any] = {}

    def create_all(self, bind: Any = None) -> None:  # pragma: no cover - no-op for stub
        return None


class DeclarativeMeta(type):
    def __new__(mcls, name: str, bases: tuple[type, ...], attrs: Dict[str, Any]):
        attrs.setdefault("__columns__", {})
        attrs.setdefault("__primary_key__", None)
        cls = super().__new__(mcls, name, bases, attrs)
        return cls

    def __init__(cls, name: str, bases: tuple[type, ...], attrs: Dict[str, Any]):
        super().__init__(name, bases, attrs)
        if not hasattr(cls, "metadata"):
            cls.metadata = Metadata()


def declarative_base() -> Type[Any]:
    class Base(metaclass=DeclarativeMeta):
        metadata = Metadata()

        def __init__(self, **kwargs: Any) -> None:
            for key, column in getattr(self, "__columns__", {}).items():
                if key in kwargs:
                    setattr(self, key, kwargs[key])
                elif column.default is not None:
                    default_value = column.default() if callable(column.default) else column.default
                    setattr(self, key, default_value)
            for key, value in kwargs.items():
                if key not in getattr(self, "__columns__", {}):
                    setattr(self, key, value)

    return Base


class Engine:
    def __init__(self) -> None:
        self.storage: Dict[Type[Any], List[Any]] = {}


def create_engine(url: str, connect_args: Optional[Dict[str, Any]] = None) -> Engine:
    return Engine()


class Query:
    def __init__(self, data: List[Any]) -> None:
        self._data = data

    def filter_by(self, **kwargs: Any) -> "Query":
        filtered = [obj for obj in self._data if all(getattr(obj, k) == v for k, v in kwargs.items())]
        return Query(filtered)

    def order_by(self, *_args: Any, **_kwargs: Any) -> "Query":
        return self

    def all(self) -> List[Any]:
        return list(self._data)

    def first(self) -> Optional[Any]:
        return self._data[0] if self._data else None


class Session:
    def __init__(self, engine: Engine) -> None:
        self.engine = engine
        self._pending: List[Any] = []

    def add(self, obj: Any) -> None:
        self._pending.append(obj)

    def commit(self) -> None:
        for obj in self._pending:
            model = obj.__class__
            pk_name = getattr(model, "__primary_key__", "id")
            if getattr(obj, pk_name, None) is None:
                current = self.engine.storage.get(model, [])
                setattr(obj, pk_name, len(current) + 1)
            self.engine.storage.setdefault(model, []).append(obj)
        self._pending.clear()

    def refresh(self, obj: Any) -> None:  # pragma: no cover - no-op for stub
        return None

    def delete(self, obj: Any) -> None:
        model = obj.__class__
        if model in self.engine.storage and obj in self.engine.storage[model]:
            self.engine.storage[model].remove(obj)

    def query(self, model: Type[Any]) -> Query:
        return Query(self.engine.storage.get(model, []))

    def get(self, model: Type[Any], obj_id: Any) -> Optional[Any]:
        for obj in self.engine.storage.get(model, []):
            if getattr(obj, getattr(model, "__primary_key__", "id"), None) == obj_id:
                return obj
        return None

    def close(self) -> None:  # pragma: no cover - no-op for stub
        return None


def sessionmaker(autocommit: bool = False, autoflush: bool = False, bind: Optional[Engine] = None):
    def factory() -> Session:
        assert bind is not None, "Engine must be provided"
        return Session(bind)

    return factory


__all__ = [
    "Boolean",
    "Column",
    "DateTime",
    "ForeignKey",
    "Integer",
    "Numeric",
    "String",
    "Text",
    "create_engine",
    "declarative_base",
    "sessionmaker",
    "Session",
]
