"""Compute a simple demand score for products."""
from core.pricing.rules import DemandRule


def compute_demand_score(product: object, rules: DemandRule) -> float:
    base_score = rules.base_score
    price_component = getattr(product, "price", 0) * rules.weight_price
    category_component = rules.weight_category
    return max(base_score + category_component - price_component * 0.01, 0)
