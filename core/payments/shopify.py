"""Shopify GraphQL Admin API gateway (simulated for offline use)."""
from __future__ import annotations

from typing import Any, Dict, Optional

import requests

from core.logging.logger import get_logger
from core.payments.base import PaymentGateway, PaymentResult

LOGGER = get_logger(__name__)


class ShopifyGateway(PaymentGateway):
    """Minimal Shopify gateway wrapper."""

    def __init__(
        self,
        *,
        shop_domain: str,
        access_token: str,
        http_client: Optional[Any] = None,
    ) -> None:
        self.shop_domain = shop_domain
        self.access_token = access_token
        self.http_client = http_client
        self.api_url = f"https://{shop_domain}/admin/api/2025-01/graphql.json"

    def _post_graphql(self, query: str, variables: Dict[str, Any]) -> Optional[PaymentResult]:
        client = self.http_client
        if client is None:
            return None
        headers = {
            "Content-Type": "application/json",
            "X-Shopify-Access-Token": self.access_token,
        }
        response = client.post(self.api_url, json={"query": query, "variables": variables}, headers=headers)
        try:
            payload = response.json()
        except Exception:  # pragma: no cover - defensive
            payload = {}
        data = payload.get("data") or {}
        if 200 <= response.status_code < 300:
            checkout = data.get("checkoutCreate", {}).get("checkout")
            if checkout and checkout.get("id"):
                return PaymentResult(success=True, payment_id=checkout["id"], status="created", raw=payload)

        errors = payload.get("errors") or data.get("checkoutCreate", {}).get("userErrors")
        return PaymentResult(success=False, message=str(errors or "request_failed"), raw=payload)

    def create_checkout_session(self, order) -> PaymentResult:
        """Create a Shopify checkout or simulate if offline."""

        mutation = """
        mutation CreateCheckout($amount: Decimal!, $currency: CurrencyCode!) {
          checkoutCreate(input: {lineItems: [{quantity: 1, price: {amount: $amount, currencyCode: $currency}}]}) {
            checkout { id }
            userErrors { field message }
          }
        }
        """
        variables = {
            "amount": float(getattr(order, "total_amount", 0)),
            "currency": getattr(order, "currency", "USD"),
        }
        result = self._post_graphql(mutation, variables)
        if result:
            return result

        simulated_id = f"shopify_checkout_{getattr(order, 'id', 'unknown')}"
        return PaymentResult(success=True, payment_id=simulated_id, status="created")

    def handle_webhook(self, payload: Dict[str, Any]) -> PaymentResult:
        data = payload.get("data", {})
        payment_id = data.get("id") or data.get("checkout_id")
        status = data.get("status")
        success = status in {"paid", "success"}
        return PaymentResult(success=success, payment_id=payment_id, status=status, raw=payload)

    def refund(self, payment_id: str, amount: Optional[float] = None) -> PaymentResult:
        mutation = """
        mutation RefundPayment($id: ID!, $amount: MoneyInput) {
          refundPayment(id: $id, amount: $amount) {
            refund { id status }
            userErrors { message field }
          }
        }
        """
        variables: Dict[str, Any] = {"id": payment_id}
        if amount is not None:
            variables["amount"] = {"amount": float(amount), "currencyCode": "USD"}

        result = self._post_graphql(mutation, variables)
        if result:
            return result

        return PaymentResult(success=True, payment_id=payment_id, status="refunded")


__all__ = ["ShopifyGateway"]
