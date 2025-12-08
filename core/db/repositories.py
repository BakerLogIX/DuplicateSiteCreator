"""Repository classes encapsulating CRUD operations for database models."""
from __future__ import annotations

from typing import Generic, List, Optional, Type, TypeVar

from sqlalchemy.orm import Session

from core.db.base import Base
from core.models.entities import (
    Image,
    Order,
    OrderItem,
    PriceRule,
    Product,
    Store,
    Supplier,
    Transaction,
    Variant,
)

ModelType = TypeVar("ModelType", bound=Base)

__all__ = [
    "BaseRepository",
    "StoreRepository",
    "ProductRepository",
    "VariantRepository",
    "ImageRepository",
    "SupplierRepository",
    "OrderRepository",
    "OrderItemRepository",
    "TransactionRepository",
    "PriceRuleRepository",
]


class BaseRepository(Generic[ModelType]):
    """Base repository providing common CRUD helpers."""

    model: Type[ModelType]

    def __init__(self, db: Session) -> None:
        self.db = db

    def get(self, obj_id: int) -> Optional[ModelType]:
        """Retrieve an object by its primary key.

        Deprecated alias for :meth:`get_by_id` kept for compatibility with
        earlier tests. Prefer :meth:`get_by_id` in new code.
        """

        return self.get_by_id(obj_id)

    def get_by_id(self, obj_id: int) -> Optional[ModelType]:
        """Retrieve an object by its primary key."""

        return self.db.get(self.model, obj_id)

    def get_all(self) -> List[ModelType]:
        """Return all records for the model."""

        return list(self.db.query(self.model).all())

    def create(self, **data) -> ModelType:
        """Create and persist a new instance."""

        obj = self.model(**data)
        self.db.add(obj)
        self.db.commit()
        self.db.refresh(obj)
        return obj

    def update(self, obj: ModelType, **data) -> ModelType:
        """Update fields on an instance and persist changes."""

        for key, value in data.items():
            setattr(obj, key, value)
        self.db.add(obj)
        self.db.commit()
        self.db.refresh(obj)
        return obj

    def delete(self, obj: ModelType) -> None:
        """Delete an instance from the database."""

        self.db.delete(obj)
        self.db.commit()


class StoreRepository(BaseRepository[Store]):
    """Repository for Store entities."""

    model = Store

    def get_by_name(self, name: str) -> Optional[Store]:
        return self.db.query(self.model).filter_by(name=name).first()


class ProductRepository(BaseRepository[Product]):
    """Repository for Product entities."""

    model = Product

    def get_by_store(self, store_id: int) -> List[Product]:
        return list(self.db.query(self.model).filter_by(store_id=store_id).all())

    def get_active_by_store(self, store_id: int) -> List[Product]:
        return list(
            self.db.query(self.model).filter_by(store_id=store_id, is_active=True).all()
        )

    def get_by_sku(self, sku: str, store_id: Optional[int] = None) -> Optional[Product]:
        """Return a product by SKU scoped to a store when provided."""

        query = self.db.query(self.model).filter_by(sku=sku)
        if store_id is not None:
            query = query.filter_by(store_id=store_id)
        return query.first()


class VariantRepository(BaseRepository[Variant]):
    """Repository for Variant entities."""

    model = Variant

    def get_by_product(self, product_id: int) -> List[Variant]:
        return list(self.db.query(self.model).filter_by(product_id=product_id).all())


class ImageRepository(BaseRepository[Image]):
    """Repository for Image entities."""

    model = Image

    def get_by_product(self, product_id: int) -> List[Image]:
        return list(self.db.query(self.model).filter_by(product_id=product_id).all())


class SupplierRepository(BaseRepository[Supplier]):
    """Repository for Supplier entities."""

    model = Supplier

    def get_by_store(self, store_id: int) -> List[Supplier]:
        return list(self.db.query(self.model).filter_by(store_id=store_id).all())

    def get_active_suppliers(self, store_id: Optional[int] = None) -> List[Supplier]:
        query = self.db.query(self.model).filter_by(active=True)
        if store_id is not None:
            query = query.filter_by(store_id=store_id)
        return list(query.order_by(self.model.id).all())


class OrderRepository(BaseRepository[Order]):
    """Repository for Order entities."""

    model = Order

    def get_by_store(self, store_id: int) -> List[Order]:
        return list(self.db.query(self.model).filter_by(store_id=store_id).all())

    def get_pending_orders(self, store_id: Optional[int] = None) -> List[Order]:
        query = self.db.query(self.model).filter_by(status="pending")
        if store_id is not None:
            query = query.filter_by(store_id=store_id)
        return list(query.all())


class OrderItemRepository(BaseRepository[OrderItem]):
    """Repository for OrderItem entities."""

    model = OrderItem

    def get_by_order(self, order_id: int) -> List[OrderItem]:
        return list(self.db.query(self.model).filter_by(order_id=order_id).all())


class TransactionRepository(BaseRepository[Transaction]):
    """Repository for Transaction entities."""

    model = Transaction

    def get_by_order(self, order_id: int) -> List[Transaction]:
        return list(self.db.query(self.model).filter_by(order_id=order_id).all())

    def get_by_store(self, store_id: int) -> List[Transaction]:
        """Return transactions associated with a specific store."""

        return list(self.db.query(self.model).filter_by(store_id=store_id).all())


class PriceRuleRepository(BaseRepository[PriceRule]):
    """Repository for PriceRule entities."""

    model = PriceRule

    def get_by_store(self, store_id: int) -> List[PriceRule]:
        return list(self.db.query(self.model).filter_by(store_id=store_id).all())

    def get_active_rules(self, store_id: Optional[int] = None) -> List[PriceRule]:
        query = self.db.query(self.model).filter_by(active=True)
        if store_id is not None:
            query = query.filter_by(store_id=store_id)
        return list(query.all())
