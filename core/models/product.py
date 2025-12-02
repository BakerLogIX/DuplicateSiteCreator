"""Product-related models."""
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field, HttpUrl
from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.db.base import Base


class Product(Base):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    store_id: Mapped[int] = mapped_column(Integer, ForeignKey("stores.id"), index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    price: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    currency: Mapped[str] = mapped_column(String(8), default="USD")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    variants: Mapped[List["Variant"]] = relationship(
        "Variant", back_populates="product", cascade="all, delete-orphan"
    )
    images: Mapped[List["Image"]] = relationship(
        "Image", back_populates="product", cascade="all, delete-orphan"
    )


class Variant(Base):
    __tablename__ = "variants"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    product_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("products.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    sku: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    price: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    stock: Mapped[int] = mapped_column(Integer, default=0)

    product: Mapped[Product] = relationship("Product", back_populates="variants")


class Image(Base):
    __tablename__ = "images"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    product_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("products.id", ondelete="CASCADE"), nullable=False
    )
    url: Mapped[str] = mapped_column(String(500), nullable=False)
    alt_text: Mapped[Optional[str]] = mapped_column(String(255))

    product: Mapped[Product] = relationship("Product", back_populates="images")


class ImageSchema(BaseModel):
    url: HttpUrl
    alt_text: Optional[str] = None


class VariantSchema(BaseModel):
    name: str
    sku: Optional[str] = None
    price: float = Field(ge=0)
    stock: int = Field(default=0, ge=0)


class ProductSchema(BaseModel):
    name: str
    description: Optional[str] = None
    price: float = Field(ge=0)
    currency: str = "USD"
    variants: List[VariantSchema] = Field(default_factory=list)
    images: List[ImageSchema] = Field(default_factory=list)

    class Config:
        orm_mode = True
