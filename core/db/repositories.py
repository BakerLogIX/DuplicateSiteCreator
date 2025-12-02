"""Repository helpers for CRUD operations."""
from typing import Generic, Iterable, Optional, Type, TypeVar

from sqlalchemy import select
from sqlalchemy.orm import Session

T = TypeVar("T")


class Repository(Generic[T]):
    """Generic repository providing common CRUD operations."""

    def __init__(self, session: Session, model: Type[T]):
        self.session = session
        self.model = model

    def get_by_id(self, obj_id: int) -> Optional[T]:
        return self.session.get(self.model, obj_id)

    def get_all(self) -> Iterable[T]:
        result = self.session.execute(select(self.model))
        return result.scalars().all()

    def create(self, **kwargs) -> T:
        instance = self.model(**kwargs)
        self.session.add(instance)
        self.session.commit()
        self.session.refresh(instance)
        return instance

    def update(self, obj_id: int, **kwargs) -> Optional[T]:
        instance = self.get_by_id(obj_id)
        if not instance:
            return None

        for key, value in kwargs.items():
            if hasattr(instance, key):
                setattr(instance, key, value)
        self.session.commit()
        self.session.refresh(instance)
        return instance

    def delete(self, obj_id: int) -> bool:
        instance = self.get_by_id(obj_id)
        if not instance:
            return False
        self.session.delete(instance)
        self.session.commit()
        return True


class ProductRepository(Repository[T]):
    def __init__(self, session: Session, model: Type[T]):
        super().__init__(session, model)

    def get_by_store(self, store_id: int) -> Iterable[T]:
        result = self.session.execute(
            select(self.model).where(getattr(self.model, "store_id") == store_id)
        )
        return result.scalars().all()


class OrderRepository(Repository[T]):
    pass


class SupplierRepository(Repository[T]):
    pass
