"""Stripe Checkout Sessions gateway (simulated for offline use)."""
from __future__ import annotations

from typing import Any, Dict, Optional

import requests

from core.logging.logger import get_logger
from core.payments.base import PaymentGateway, PaymentResult

LOGGER = get_logger(__name__)


class StripeGateway(PaymentGateway):
    """Minimal Stripe gateway wrapper."""

    def __init__(
        self,
        *,
        api_key: str,
        success_url: str,
        cancel_url: str,
        http_client: Optional[Any] = None,
    ) -> None:
        self.api_key = api_key
        self.success_url = success_url
        self.cancel_url = cancel_url
        self.http_client = http_client  # injectable for tests
        self.api_base = "https://api.stripe.com"

    def _post(self, path: str, data: Dict[str, Any]) -> Optional[PaymentResult]:
        client = self.http_client
        if client is None:
            return None
        url = f"{self.api_base}{path}"
        headers = {"Authorization": f"Bearer {self.api_key}"}
        response = client.post(url, data=data, headers=headers)
        try:
            payload = response.json()
        except Exception:  # pragma: no cover - defensive
            payload = {}
        if 200 <= response.status_code < 300:
            return PaymentResult(
                success=True,
                payment_id=str(payload.get("id")),
                status=str(payload.get("status", "created")),
                raw=payload,
            )
        return PaymentResult(
            success=False,
            message=str(payload.get("error", "request_failed")),
            raw=payload,
        )

    def create_checkout_session(self, order) -> PaymentResult:
        """Create a Checkout Session or simulate if offline."""

        payload = {
            "success_url": self.success_url,
            "cancel_url": self.cancel_url,
            "mode": "payment",
            "line_items[0][price_data][currency]": getattr(order, "currency", "USD"),
            "line_items[0][price_data][product_data][name]": getattr(order, "customer_name", "Order"),
            "line_items[0][price_data][unit_amount]": int(float(getattr(order, "total_amount", 0)) * 100),
            "line_items[0][quantity]": 1,
        }

        result = self._post("/v1/checkout/sessions", payload)
        if result:
            return result

        simulated_id = f"cs_test_{getattr(order, 'id', 'unknown')}"
        return PaymentResult(success=True, payment_id=simulated_id, status="created")

    def handle_webhook(self, payload: Dict[str, Any]) -> PaymentResult:
        event_type = payload.get("type", "")
        data_object = payload.get("data", {}).get("object", {})
        payment_id = data_object.get("id")
        status = data_object.get("payment_status") or data_object.get("status")
        success = event_type == "checkout.session.completed"
        return PaymentResult(success=success, payment_id=payment_id, status=status, raw=payload)

    def refund(self, payment_id: str, amount: Optional[float] = None) -> PaymentResult:
        payload: Dict[str, Any] = {"payment_intent": payment_id}
        if amount is not None:
            payload["amount"] = int(float(amount) * 100)

        result = self._post("/v1/refunds", payload)
        if result:
            return result

        return PaymentResult(success=True, payment_id=payment_id, status="refunded")


__all__ = ["StripeGateway"]
