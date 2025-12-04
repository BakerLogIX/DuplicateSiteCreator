"""Payment gateway abstractions and factory helpers."""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, Optional

from core.logging.logger import get_logger

LOGGER = get_logger(__name__)


@dataclass
class PaymentResult:
    """Lightweight result wrapper for gateway operations."""

    success: bool
    payment_id: Optional[str] = None
    status: Optional[str] = None
    message: Optional[str] = None
    raw: Optional[Dict[str, Any]] = None


class PaymentGateway(ABC):
    """Interface for payment gateways."""

    @abstractmethod
    def create_checkout_session(self, order) -> PaymentResult:
        """Create a checkout/payment session for an order."""

    @abstractmethod
    def handle_webhook(self, payload: Dict[str, Any]) -> PaymentResult:
        """Handle webhook callbacks from the gateway."""

    @abstractmethod
    def refund(self, payment_id: str, amount: Optional[float] = None) -> PaymentResult:
        """Refund a payment by identifier."""


def build_payment_gateway(provider: Optional[str], config: Dict[str, Any]) -> Optional[PaymentGateway]:
    """Instantiate a gateway based on provider and config.

    Args:
        provider: Gateway identifier (e.g., ``stripe`` or ``shopify``).
        config: Payments configuration dictionary, typically from ``config.yaml``.
    """

    if not provider:
        return None
    provider = provider.lower()

    if provider == "stripe":
        from core.payments.stripe import StripeGateway

        stripe_cfg = config.get("stripe", {})
        return StripeGateway(
            api_key=stripe_cfg.get("secret_key", "test_key"),
            success_url=stripe_cfg.get("success_url", "https://example.com/success"),
            cancel_url=stripe_cfg.get("cancel_url", "https://example.com/cancel"),
        )

    if provider == "shopify":
        from core.payments.shopify import ShopifyGateway

        shopify_cfg = config.get("shopify", {})
        return ShopifyGateway(
            shop_domain=shopify_cfg.get("shop_domain", "example.myshopify.com"),
            access_token=shopify_cfg.get("access_token", "test_token"),
        )

    LOGGER.warning("Unknown payment provider '%s'; no gateway instantiated", provider)
    return None


__all__ = ["PaymentGateway", "PaymentResult", "build_payment_gateway"]
