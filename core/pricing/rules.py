"""Rule definitions for the pricing engine."""
from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from typing import Dict, Optional


@dataclass
class MarginRule:
    """Represents a margin band that can be applied to a product.

    Attributes:
        min_margin: The minimum margin percentage expressed as a decimal (e.g. 0.1 for 10%).
        max_margin: The maximum margin percentage expressed as a decimal (e.g. 0.3 for 30%).
        category: Optional category filter that restricts the rule to matching products.
        price_min: Lower bound for the product's base price to qualify for the rule.
        price_max: Upper bound for the product's base price to qualify for the rule.
    """

    min_margin: float
    max_margin: float
    category: Optional[str] = None
    price_min: Optional[float] = None
    price_max: Optional[float] = None

    def applies_to(self, product) -> bool:
        """Return True if the rule should be applied to the given product."""

        if self.category:
            if not getattr(product, "category", None):
                return False
            if self.category.lower() != str(product.category).lower():
                return False

        base_price = float(Decimal(str(getattr(product, "price", 0))))
        if self.price_min is not None and base_price < self.price_min:
            return False
        if self.price_max is not None and base_price > self.price_max:
            return False
        return True

    def margin_for_score(self, demand_score: float) -> float:
        """Map a demand score between 0 and 1 to a margin within the configured band."""

        score = max(0.0, min(demand_score, 1.0))
        margin_span = max(0.0, self.max_margin - self.min_margin)
        return self.min_margin + margin_span * score


@dataclass
class DemandRule:
    """Weights that influence how demand is scored for a product."""

    base_weight: float = 0.4
    price_weight: float = 0.4
    category_weight: float = 0.2
    price_anchor: float = 100.0
    category_multipliers: Dict[str, float] = field(default_factory=dict)

    def category_score(self, category: Optional[str]) -> float:
        """Return a score contribution for a category, if configured."""

        if not category:
            return 0.0
        return self.category_multipliers.get(category.lower(), 0.0)
