"""Pydantic-style schemas for core entities."""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class ORMModel(BaseModel):
    """Base schema enabling ORM compatibility for Pydantic v1 and v2."""

    model_config = ConfigDict(from_attributes=True)


class StoreSchema(ORMModel):
    id: Optional[int] = None
    name: str
    theme: str = "default"
    payment_provider: Optional[str] = None
    default_currency: str = "USD"
    timezone: str = "UTC"
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class ProductSchema(ORMModel):
    id: Optional[int] = None
    store_id: int
    name: str
    description: Optional[str] = None
    sku: Optional[str] = None
    price: float
    currency: str = "USD"
    category: Optional[str] = None
    supplier_price: Optional[float] = None
    inventory_count: int = 0
    pricing_outdated: bool = False
    is_active: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class VariantSchema(ORMModel):
    id: Optional[int] = None
    product_id: int
    name: str
    sku: Optional[str] = None
    price: float
    inventory_count: int = 0
    is_default: bool = False


class ImageSchema(ORMModel):
    id: Optional[int] = None
    product_id: int
    url: str
    alt_text: Optional[str] = None
    position: Optional[int] = None


class SupplierSchema(ORMModel):
    id: Optional[int] = None
    store_id: int
    name: str
    contact_email: Optional[str] = None
    api_endpoint: Optional[str] = None
    active: bool = True


class OrderSchema(ORMModel):
    id: Optional[int] = None
    store_id: int
    status: str = "pending"
    total_amount: float
    currency: str = "USD"
    customer_name: Optional[str] = None
    customer_email: Optional[str] = None
    tracking_number: Optional[str] = None
    status_message: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class OrderItemSchema(ORMModel):
    id: Optional[int] = None
    order_id: int
    product_id: int
    variant_id: Optional[int] = None
    supplier_id: Optional[int] = None
    quantity: int = 1
    unit_price: float
    total_price: float
    status: str = "pending"
    tracking_number: Optional[str] = None


class TransactionSchema(ORMModel):
    id: Optional[int] = None
    order_id: int
    amount: float
    currency: str = "USD"
    status: str = "pending"
    transaction_type: str = "charge"
    gateway_reference: Optional[str] = None
    created_at: Optional[datetime] = None


class PriceRuleSchema(ORMModel):
    id: Optional[int] = None
    store_id: int
    name: str
    rule_type: str = "margin"
    value: float
    active: bool = True
    starts_at: Optional[datetime] = None
    ends_at: Optional[datetime] = None
