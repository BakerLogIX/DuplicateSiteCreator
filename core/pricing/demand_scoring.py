"""Compute demand scores for products using configured rules."""
from __future__ import annotations

from decimal import Decimal

from core.pricing.rules import DemandRule


def compute_demand_score(product, rules: DemandRule) -> float:
    """Return a normalized demand score for the provided product.

    The score is based on the weighted contribution of:
    - A baseline weight that prevents scores from reaching zero.
    - The relative price compared to a configurable anchor value (cheaper products are
      assumed to have higher demand).
    - Category-specific multipliers.
    """

    if rules.price_anchor <= 0:
        raise ValueError("price_anchor must be positive")

    price_value = float(Decimal(str(getattr(product, "price", 0))))
    normalized_price = max(0.0, min(1.0, 1 - (price_value / rules.price_anchor)))
    category_component = rules.category_score(getattr(product, "category", None))

    weighted_score = (
        rules.base_weight
        + normalized_price * rules.price_weight
        + category_component * rules.category_weight
    )
    total_weight = rules.base_weight + rules.price_weight + rules.category_weight
    if total_weight <= 0:
        return 0.0

    return max(0.0, min(weighted_score / total_weight, 1.0))
