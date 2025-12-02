"""Pricing rule definitions."""
from dataclasses import dataclass
from typing import Optional


@dataclass
class MarginRule:
    min_margin: float
    max_margin: float
    category: Optional[str] = None
    price_band: Optional[tuple[float, float]] = None


@dataclass
class DemandRule:
    weight_price: float = 1.0
    weight_category: float = 1.0
    base_score: float = 1.0
