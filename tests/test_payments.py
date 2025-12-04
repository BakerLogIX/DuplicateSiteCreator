from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict

from core.payments.base import PaymentResult, build_payment_gateway
from core.payments.shopify import ShopifyGateway
from core.payments.stripe import StripeGateway


@dataclass
class DummyOrder:
    id: int
    total_amount: float
    currency: str = "USD"
    customer_name: str = "Customer"


class FakeResponse:
    def __init__(self, status_code: int, payload: Dict[str, Any]):
        self.status_code = status_code
        self._payload = payload

    def json(self) -> Dict[str, Any]:
        return self._payload


class FakeHTTPClient:
    def __init__(self, response: FakeResponse):
        self.response = response
        self.last_request: Dict[str, Any] | None = None

    def post(self, url: str, data=None, json=None, headers=None):
        self.last_request = {"url": url, "data": data, "json": json, "headers": headers}
        return self.response


def test_stripe_checkout_simulated() -> None:
    order = DummyOrder(id=1, total_amount=25.5)
    gateway = StripeGateway(api_key="sk_test", success_url="https://ok", cancel_url="https://cancel")
    result = gateway.create_checkout_session(order)
    assert result.success is True
    assert result.payment_id.startswith("cs_test_")


def test_stripe_checkout_failure_via_http() -> None:
    order = DummyOrder(id=2, total_amount=10)
    client = FakeHTTPClient(FakeResponse(400, {"error": "bad_request"}))
    gateway = StripeGateway(
        api_key="sk_test", success_url="https://ok", cancel_url="https://cancel", http_client=client
    )
    result = gateway.create_checkout_session(order)
    assert result.success is False
    assert result.message == "bad_request"


def test_shopify_checkout_success_via_http() -> None:
    payload = {
        "data": {"checkoutCreate": {"checkout": {"id": "gid://shopify/Checkout/1"}, "userErrors": []}}
    }
    client = FakeHTTPClient(FakeResponse(200, payload))
    gateway = ShopifyGateway(shop_domain="example.myshopify.com", access_token="token", http_client=client)
    result = gateway.create_checkout_session(DummyOrder(id=3, total_amount=15))
    assert result.success is True
    assert result.payment_id.endswith("/1")
    assert "example.myshopify.com" in client.last_request["url"]


def test_shopify_refund_failure_via_http() -> None:
    payload = {"errors": [{"message": "forbidden"}]}
    client = FakeHTTPClient(FakeResponse(403, payload))
    gateway = ShopifyGateway(shop_domain="example.myshopify.com", access_token="token", http_client=client)
    result = gateway.refund("gid://shopify/Payment/1", amount=5)
    assert result.success is False
    assert "forbidden" in str(result.message)


def test_gateway_factory_builds_correct_gateway() -> None:
    config = {
        "stripe": {"secret_key": "sk_test", "success_url": "https://ok", "cancel_url": "https://cancel"},
        "shopify": {"shop_domain": "demo.myshopify.com", "access_token": "token"},
    }
    stripe_gateway = build_payment_gateway("stripe", config)
    shopify_gateway = build_payment_gateway("shopify", config)

    assert isinstance(stripe_gateway, StripeGateway)
    assert isinstance(shopify_gateway, ShopifyGateway)

