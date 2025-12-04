"""Heuristics for identifying product and category pages."""
from __future__ import annotations

import re
from bs4 import BeautifulSoup


_PRICE_RE = re.compile(r"\b\d+[.,]?\d*\s*(?:[$€£]|usd|eur|gbp)", re.I)


def _contains_price(text: str) -> bool:
    return bool(_PRICE_RE.search(text))


def is_product_page(html: str) -> bool:
    """Return True if the HTML resembles a product detail page."""

    soup = BeautifulSoup(html, "html.parser")
    text = soup.get_text(" ", strip=True).lower()

    has_price_hint = _contains_price(text) or bool(
        soup.select_one('[itemprop="price"], .price, .product-price')
    )
    has_cart_call_to_action = bool(
        soup.find("button", string=re.compile("add to cart", re.I))
        or soup.find("form", {"id": re.compile("add-to-cart", re.I)})
        or soup.find("button", {"name": re.compile("add", re.I)})
    )
    has_schema_product = bool(soup.find(attrs={"itemtype": re.compile("Product", re.I)}))

    return (has_price_hint and has_cart_call_to_action) or has_schema_product


def is_category_page(html: str) -> bool:
    """Return True if the HTML resembles a category/listing page."""

    soup = BeautifulSoup(html, "html.parser")
    product_cards = soup.select(".product-card, .product-item, [data-product-id]")
    grid = soup.select_one(".product-grid, .collection-grid, ul.products")
    multiple_prices = len(_PRICE_RE.findall(soup.get_text(" ", strip=True))) >= 3
    return (grid and product_cards) or multiple_prices


__all__ = ["is_product_page", "is_category_page"]
