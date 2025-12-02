"""Order and supplier models."""
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field
from sqlalchemy import DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.db.base import Base


class Supplier(Base):
    __tablename__ = "suppliers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    api_endpoint: Mapped[Optional[str]] = mapped_column(String(255))
    contact_email: Mapped[Optional[str]] = mapped_column(String(255))

    orders: Mapped[List["Order"]] = relationship("Order", back_populates="supplier")


class Order(Base):
    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    store_id: Mapped[int] = mapped_column(Integer, ForeignKey("stores.id"))
    supplier_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("suppliers.id"))
    status: Mapped[str] = mapped_column(String(50), default="pending")
    total_price: Mapped[float] = mapped_column(Float, default=0.0)
    currency: Mapped[str] = mapped_column(String(8), default="USD")
    tracking_number: Mapped[Optional[str]] = mapped_column(String(128))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    items: Mapped[List["OrderItem"]] = relationship(
        "OrderItem", back_populates="order", cascade="all, delete-orphan"
    )
    transactions: Mapped[List["Transaction"]] = relationship(
        "Transaction", back_populates="order", cascade="all, delete-orphan"
    )
    store = relationship("Store", back_populates="orders")
    supplier = relationship("Supplier", back_populates="orders")


class OrderItem(Base):
    __tablename__ = "order_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    order_id: Mapped[int] = mapped_column(Integer, ForeignKey("orders.id", ondelete="CASCADE"))
    product_id: Mapped[int] = mapped_column(Integer, ForeignKey("products.id"))
    quantity: Mapped[int] = mapped_column(Integer, default=1)
    price: Mapped[float] = mapped_column(Float, default=0.0)

    order = relationship("Order", back_populates="items")
    product = relationship("Product")


class Transaction(Base):
    __tablename__ = "transactions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    order_id: Mapped[int] = mapped_column(Integer, ForeignKey("orders.id", ondelete="CASCADE"))
    amount: Mapped[float] = mapped_column(Float, default=0.0)
    status: Mapped[str] = mapped_column(String(50), default="pending")
    provider: Mapped[Optional[str]] = mapped_column(String(50))
    reference: Mapped[Optional[str]] = mapped_column(String(128))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    order = relationship("Order", back_populates="transactions")


class SupplierSchema(BaseModel):
    name: str
    api_endpoint: Optional[str] = None
    contact_email: Optional[str] = None

    class Config:
        orm_mode = True


class OrderItemSchema(BaseModel):
    product_id: int
    quantity: int = Field(default=1, ge=1)
    price: float = Field(default=0.0, ge=0)


class OrderSchema(BaseModel):
    store_id: int
    supplier_id: Optional[int] = None
    status: str = "pending"
    total_price: float = Field(default=0.0, ge=0)
    currency: str = "USD"
    tracking_number: Optional[str] = None
    items: List[OrderItemSchema] = Field(default_factory=list)

    class Config:
        orm_mode = True
