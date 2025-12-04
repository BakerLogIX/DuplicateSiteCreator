"""Machine-learning plugin interface and baseline LightGBM implementation."""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from decimal import Decimal
from typing import Any, Dict, Iterable, List, Optional, Sequence

from core.logging.logger import get_logger
from core.pricing.demand_scoring import compute_demand_score
from core.pricing.rules import DemandRule

LOGGER = get_logger(__name__)


class PricingMLPlugin(ABC):
    """Interface for machine-learning driven pricing plugins."""

    @abstractmethod
    def fit(self, training_data: Iterable[Dict[str, Any]]) -> None:
        """Train the model using the provided data."""

    @abstractmethod
    def predict_margin(self, product) -> Optional[float]:
        """Return a margin multiplier for the given product."""

    @property
    @abstractmethod
    def trained(self) -> bool:
        """True when the model is ready to serve predictions."""


def _extract_feature_row(record: Dict[str, Any]) -> Optional[List[float]]:
    """Convert a training record into a numeric feature row."""

    try:
        price = float(Decimal(str(record.get("price", 0))))
        supplier_price = float(Decimal(str(record.get("supplier_price", record.get("cost", 0)))))
        inventory = float(record.get("inventory_count", record.get("inventory", 0)) or 0)
        demand = float(record.get("demand_score", 0.0))
    except (ArithmeticError, ValueError, TypeError):
        return None
    return [price, supplier_price, inventory, demand]


@dataclass
class LightGBMMarginPlugin(PricingMLPlugin):
    """Baseline LightGBM-powered pricing plugin with graceful fallback."""

    demand_rule: DemandRule = field(default_factory=DemandRule)
    n_estimators: int = 50
    learning_rate: float = 0.1
    random_state: int = 42

    def __post_init__(self) -> None:
        self._model = None
        self._trained = False
        self._fallback_margin = 0.2

    @property
    def trained(self) -> bool:
        return bool(self._trained)

    def fit(self, training_data: Iterable[Dict[str, Any]]) -> None:
        """Train a LightGBM regressor or compute a fallback average margin."""

        data = list(training_data or [])
        feature_rows: List[List[float]] = []
        targets: List[float] = []

        for record in data:
            features = _extract_feature_row(record)
            target = record.get("margin") if "margin" in record else record.get("target_margin")
            if features is None or target is None:
                continue
            try:
                targets.append(float(target))
                feature_rows.append(features)
            except (ArithmeticError, ValueError, TypeError):
                continue

        if not targets or not feature_rows:
            LOGGER.warning("No valid training data supplied to LightGBMMarginPlugin")
            self._trained = False
            return

        try:
            import lightgbm as lgb  # type: ignore
        except ModuleNotFoundError:
            self._fallback_margin = sum(targets) / len(targets)
            self._trained = True
            LOGGER.info("LightGBM not installed; using average margin fallback")
            return

        try:
            self._model = lgb.LGBMRegressor(
                n_estimators=self.n_estimators,
                learning_rate=self.learning_rate,
                random_state=self.random_state,
            )
            self._model.fit(feature_rows, targets)
            self._trained = True
        except Exception as exc:  # pragma: no cover - defensive path
            LOGGER.warning("Failed to train LightGBM model, falling back to average margin: %s", exc)
            self._fallback_margin = sum(targets) / len(targets)
            self._model = None
            self._trained = True

    def _feature_vector_for_product(self, product) -> List[float]:
        demand_score = compute_demand_score(product, self.demand_rule)
        price = float(Decimal(str(getattr(product, "price", 0))))
        supplier_price = float(Decimal(str(getattr(product, "supplier_price", 0) or 0)))
        inventory = float(getattr(product, "inventory_count", 0) or 0)
        return [price, supplier_price, inventory, demand_score]

    def predict_margin(self, product) -> Optional[float]:
        if not self.trained:
            return None

        features = [self._feature_vector_for_product(product)]

        if self._model:
            prediction = self._model.predict(features)[0]
            return max(0.0, float(prediction))

        return max(0.0, float(self._fallback_margin))
