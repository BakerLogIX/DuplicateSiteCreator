"""Pricing models."""
from typing import Optional

from pydantic import BaseModel, Field
from sqlalchemy import Float, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from core.db.base import Base


class PriceRule(Base):
    __tablename__ = "price_rules"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    category: Mapped[Optional[str]] = mapped_column(String(255))
    min_margin: Mapped[float] = mapped_column(Float, default=0.0)
    max_margin: Mapped[float] = mapped_column(Float, default=0.0)
    demand_weight: Mapped[float] = mapped_column(Float, default=1.0)


class MarginRule(BaseModel):
    name: str
    category: Optional[str] = None
    min_margin: float = Field(default=0.0, ge=0)
    max_margin: float = Field(default=0.0, ge=0)
    demand_weight: float = Field(default=1.0, ge=0)

    class Config:
        orm_mode = True
