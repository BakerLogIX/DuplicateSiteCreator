"""Rule-based pricing engine that adjusts product prices by store."""
from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP
from typing import Iterable, List, Optional, Sequence

from sqlalchemy.orm import Session

from core.db.base import SessionLocal
from core.db.repositories import PriceRuleRepository, ProductRepository, StoreRepository
from core.logging.logger import get_logger
from core.pricing.demand_scoring import compute_demand_score
from core.pricing.rules import DemandRule, MarginRule

LOGGER = get_logger(__name__)


def _select_margin_rule(product, rules: Sequence[MarginRule]) -> MarginRule:
    for rule in rules:
        if rule.applies_to(product):
            return rule
    # Fallback rule if no specific match is found.
    return MarginRule(min_margin=0.1, max_margin=0.3)


def _build_margin_rules_from_db(db: Session, store_id: int) -> List[MarginRule]:
    rule_repo = PriceRuleRepository(db)
    margin_rules: List[MarginRule] = []
    for rule in rule_repo.get_active_rules(store_id=store_id):
        if rule.rule_type != "margin":
            continue
        margin_value = float(rule.value) / 100
        margin_rules.append(
            MarginRule(
                min_margin=margin_value,
                max_margin=margin_value,
                category=None,
                price_min=None,
                price_max=None,
            )
        )

    if not margin_rules:
        margin_rules.append(MarginRule(min_margin=0.1, max_margin=0.3))
    return margin_rules


def _apply_margin(price: Decimal, margin: float) -> Decimal:
    multiplier = Decimal("1") + Decimal(str(margin))
    return (price * multiplier).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def run_pricing(
    store_id: int,
    *,
    db: Optional[Session] = None,
    margin_rules: Optional[Iterable[MarginRule]] = None,
    demand_rule: Optional[DemandRule] = None,
) -> List:
    """Execute pricing for all active products in the specified store.

    Args:
        store_id: Identifier of the target store.
        db: Optional SQLAlchemy session. If omitted, a new session is created and closed.
        margin_rules: Optional iterable of :class:`MarginRule` instances to override
            database-configured rules.
        demand_rule: Optional :class:`DemandRule` instance controlling demand scoring.

    Returns:
        List of updated product instances.

    Raises:
        ValueError: If the store does not exist.
    """

    session = db or SessionLocal()
    created_session = db is None
    try:
        store = StoreRepository(session).get_by_id(store_id)
        if not store:
            raise ValueError(f"Store with id {store_id} not found")

        product_repo = ProductRepository(session)
        products = product_repo.get_active_by_store(store_id)
        if not products:
            LOGGER.info("No active products found for store %s", store_id)
            return []

        rules_to_apply = list(margin_rules) if margin_rules else _build_margin_rules_from_db(session, store_id)
        demand_rules = demand_rule or DemandRule()

        updated_products = []
        for product in products:
            demand_score = compute_demand_score(product, demand_rules)
            rule = _select_margin_rule(product, rules_to_apply)
            new_price = _apply_margin(Decimal(str(product.price)), rule.margin_for_score(demand_score))
            product_repo.update(product, price=new_price)
            updated_products.append(product)
            LOGGER.debug(
                "Priced product %s with demand %.2f using margin %.2f -> %s",
                product.id,
                demand_score,
                rule.margin_for_score(demand_score),
                new_price,
            )

        return updated_products
    finally:
        if created_session:
            session.close()
