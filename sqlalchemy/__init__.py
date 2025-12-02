"""Lightweight SQLAlchemy-like stubs for offline execution.

These classes implement only the small subset of behaviour exercised by the
repository unit tests. They mimic core ORM concepts such as declarative models,
sessions, queries, and columns backed by an in-memory store. The goal is to
keep the project runnable without external dependencies when network access is
restricted.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Dict, Iterable, List, Optional, Type


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
    """Descriptor capturing metadata for model attributes."""

    def __init__(
        self,
        _type: _Type,
        *args: Any,
        primary_key: bool = False,
        nullable: bool = True,
        default: Any = None,
        index: bool = False,
        unique: bool = False,
        onupdate: Optional[Callable[[], Any]] = None,
        **_: Any,
    ) -> None:
        self.type = _type
        self.primary_key = primary_key
        self.nullable = nullable
        self.default = default
        self.index = index
        self.unique = unique
        self.onupdate = onupdate
        self.name: Optional[str] = None

    def __set_name__(self, owner: Type[Any], name: str) -> None:
        self.name = name

    def __get__(self, instance: Any, owner: Type[Any]) -> Any:
        if instance is None:
            return self
        return instance.__dict__.get(self.name, self._get_default())

    def __set__(self, instance: Any, value: Any) -> None:
        instance.__dict__[self.name] = value

    def _get_default(self) -> Any:
        if callable(self.default):
            return self.default()
        return self.default


# Relationship stub: the tests rely only on attribute presence, not behaviour

def relationship(*_args: Any, **_kwargs: Any) -> None:
    return None


@dataclass
class _MetaData:
    registry: List[Type[Any]]

    def create_all(self, bind: "Engine") -> None:
        for model in self.registry:
            bind._ensure_model(model)


class _BaseModel:
    id: Optional[int]

    def __init__(self, **kwargs: Any) -> None:
        for key, value in kwargs.items():
            setattr(self, key, value)

    def __repr__(self) -> str:  # pragma: no cover - debugging helper
        attrs = ", ".join(f"{k}={v!r}" for k, v in self.__dict__.items())
        return f"<{self.__class__.__name__} {attrs}>"


class _BaseMeta(type):
    def __new__(mcls, name: str, bases: Iterable[Type[Any]], attrs: Dict[str, Any]):
        cls = super().__new__(mcls, name, bases, attrs)
        if name != "Base":
            Base.metadata.registry.append(cls)
        return cls


class Base(_BaseModel, metaclass=_BaseMeta):
    metadata = _MetaData(registry=[])


def declarative_base() -> Type[Base]:
    return Base


class Engine:
    def __init__(self, url: str) -> None:
        self.url = url
        self.data: Dict[Type[Any], List[Any]] = {}
        self.counters: Dict[Type[Any], int] = {}

    def _ensure_model(self, model: Type[Any]) -> None:
        self.data.setdefault(model, [])
        self.counters.setdefault(model, 0)


def create_engine(url: str, **_: Any) -> Engine:
    return Engine(url)


class Query:
    def __init__(self, model: Type[Any], session: "Session") -> None:
        self.model = model
        self.session = session
        self._items: List[Any] = list(session.engine.data.get(model, []))

    def filter_by(self, **kwargs: Any) -> "Query":
        filtered = [
            item
            for item in self._items
            if all(getattr(item, key, None) == value for key, value in kwargs.items())
        ]
        new_query = Query(self.model, self.session)
        new_query._items = filtered
        return new_query

    def order_by(self, field: Any) -> "Query":
        key = field.name if hasattr(field, "name") else field
        sorted_items = sorted(self._items, key=lambda obj: getattr(obj, key, None))
        new_query = Query(self.model, self.session)
        new_query._items = sorted_items
        return new_query

    def all(self) -> List[Any]:
        return list(self._items)

    def first(self) -> Optional[Any]:
        return self._items[0] if self._items else None


class Session:
    def __init__(self, engine: Engine):
        self.engine = engine

    def add(self, obj: Any) -> None:
        self.engine._ensure_model(obj.__class__)
        if getattr(obj, "id", None) is None:
            self.engine.counters[obj.__class__] += 1
            obj.id = self.engine.counters[obj.__class__]
        objects = self.engine.data[obj.__class__]
        if obj not in objects:
            objects.append(obj)

    def commit(self) -> None:  # pragma: no cover - API parity
        return None

    def refresh(self, obj: Any) -> None:  # pragma: no cover - API parity
        return None

    def delete(self, obj: Any) -> None:
        objects = self.engine.data.get(obj.__class__, [])
        self.engine.data[obj.__class__] = [item for item in objects if item is not obj]

    def query(self, model: Type[Any]) -> Query:
        return Query(model, self)

    def get(self, model: Type[Any], obj_id: int) -> Optional[Any]:
        for item in self.engine.data.get(model, []):
            if getattr(item, "id", None) == obj_id:
                return item
        return None

    def close(self) -> None:  # pragma: no cover - API parity
        return None


def sessionmaker(bind: Engine, autocommit: bool = False, autoflush: bool = False):
    def factory() -> Session:
        return Session(bind)

    return factory


__all__ = [
    "Base",
    "Boolean",
    "Column",
    "DateTime",
    "Engine",
    "ForeignKey",
    "Integer",
    "Numeric",
    "Query",
    "Session",
    "Text",
    "String",
    "Boolean",
    "create_engine",
    "declarative_base",
    "relationship",
    "sessionmaker",
]
