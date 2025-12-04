"""Controller helpers to trigger the pricing engine from a GUI layer."""
from __future__ import annotations

from typing import Iterable, Optional, Sequence

from sqlalchemy.orm import Session

from core.logging.logger import get_logger
from core.pricing.engine import run_pricing
from core.pricing.rules import DemandRule, MarginRule

LOGGER = get_logger(__name__)


def run_pricing_for_store(
    store_id: int,
    *,
    db: Optional[Session] = None,
    margin_rules: Optional[Iterable[MarginRule]] = None,
    demand_rule: Optional[DemandRule] = None,
    ml_plugin=None,
    ml_training_data=None,
) -> Sequence:
    """Invoke the pricing engine for the provided store and return updated products."""

    LOGGER.info("Running pricing for store %s", store_id)
    updated = run_pricing(
        store_id,
        db=db,
        margin_rules=margin_rules,
        demand_rule=demand_rule,
        ml_plugin=ml_plugin,
        ml_training_data=ml_training_data,
    )
    LOGGER.info("Pricing completed for store %s; %d products updated", store_id, len(updated))
    return updated


class PricingController:
    """Thin wrapper suitable for GUI interactions."""

    def __init__(
        self,
        db: Optional[Session] = None,
        *,
        margin_rules: Optional[Iterable[MarginRule]] = None,
        demand_rule: Optional[DemandRule] = None,
        ml_plugin=None,
        ml_training_data=None,
    ) -> None:
        self.db = db
        self.margin_rules = margin_rules
        self.demand_rule = demand_rule
        self.ml_plugin = ml_plugin
        self.ml_training_data = ml_training_data

    def run_pricing(self, store_id: int):
        """Run pricing with the configured dependencies."""

        return run_pricing_for_store(
            store_id,
            db=self.db,
            margin_rules=self.margin_rules,
            demand_rule=self.demand_rule,
            ml_plugin=self.ml_plugin,
            ml_training_data=self.ml_training_data,
        )


__all__ = ["run_pricing_for_store", "PricingController"]
