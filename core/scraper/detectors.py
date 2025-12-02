"""Heuristics to detect page types during scraping."""
from __future__ import annotations

import re
from html import unescape

PRICE_PATTERN = re.compile(r"\$?\d+[\.,]\d{2}")


def _lower_text(html: str) -> str:
    cleaned = re.sub(r"<[^>]+>", " ", html)
    return " ".join(unescape(cleaned).lower().split())


def detect_product_page(html: str) -> bool:
    """Return True if the HTML appears to represent a product page."""

    text = _lower_text(html)
    if "add to cart" in text or "buy now" in text:
        return True

    if re.search(r"itemprop\s*=\s*\"?price\"?", html, re.I):
        return True

    if re.search(r'itemtype\s*=\s*"[^"]*product[^"]*"', html, re.I):
        return True

    price_classes = re.search(r'class="[^"]*(price|product-price)[^"]*"', html, re.I)
    if price_classes:
        return True

    return bool(PRICE_PATTERN.search(text))


def detect_category_page(html: str) -> bool:
    """Simple heuristic to identify a category or listing page."""

    if re.search(r"<h1[^>]*>[^<]*category[^<]*</h1>", html, re.I):
        return True

    product_cards = re.findall(r'class="[^"]*(product-card|product-item|grid-item)[^"]*"', html, re.I)
    return len(product_cards) >= 2
