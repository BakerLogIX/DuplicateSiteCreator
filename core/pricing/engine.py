"""Pricing engine that adjusts product prices based on simple rules."""
from sqlalchemy.orm import Session

from core.config import settings
from core.models import Product
from core.pricing.demand_scoring import compute_demand_score
from core.pricing.rules import DemandRule


def run_pricing(session: Session, store_id: int) -> None:
    default_margin = settings.get_default_margin()
    rules = DemandRule()
    products = (
        session.query(Product).filter(Product.store_id == store_id).all()
    )

    for product in products:
        score = compute_demand_score(product, rules)
        multiplier = 1 + default_margin + score * 0.01
        product.price = round(product.price * multiplier, 2)
    session.commit()
