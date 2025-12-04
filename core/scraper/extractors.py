"""Extract product data from HTML pages."""
from __future__ import annotations

import re
from decimal import Decimal, InvalidOperation
from typing import Dict, List, Optional

from bs4 import BeautifulSoup


def _first_text(soup: BeautifulSoup, selectors: List[str]) -> Optional[str]:
    for selector in selectors:
        node = soup.select_one(selector)
        if node and node.get_text(strip=True):
            return node.get_text(strip=True)
    return None


def _parse_price(text: str) -> Optional[Decimal]:
    match = re.search(r"([0-9]+[.,]?[0-9]*)", text)
    if not match:
        return None
    candidate = match.group(1).replace(",", "")
    try:
        return Decimal(candidate)
    except (InvalidOperation, ValueError):
        return None


def _extract_meta(soup: BeautifulSoup, name: str) -> Optional[str]:
    tag = soup.find("meta", property=name) or soup.find("meta", attrs={"name": name})
    content = tag.get("content") if tag else None
    if content:
        return content.strip()
    return None


def extract_product_data(html: str, url: str) -> Dict[str, object]:
    """Return a normalized product payload."""

    soup = BeautifulSoup(html, "html.parser")

    name = _extract_meta(soup, "og:title") or _first_text(
        soup, ["h1.product-title", "h1", ".product-title"]
    )

    price_text = (
        _extract_meta(soup, "product:price:amount")
        or _first_text(soup, ['[itemprop="price"]', ".price", ".product-price"])
        or ""
    )
    price_value = _parse_price(price_text) or _parse_price(soup.get_text(" ", strip=True)) or Decimal(
        "0"
    )

    description = (
        _extract_meta(soup, "og:description")
        or _first_text(soup, [".product-description", "[itemprop='description']", "p"])
        or ""
    )

    category = _extract_meta(soup, "product:category") or _first_text(
        soup, [".breadcrumb .active", ".category", ".product-category"]
    )

    sku = _extract_meta(soup, "product:retailer_item_id") or _first_text(
        soup, ['[itemprop="sku"]', "#sku", ".sku"]
    )

    images: List[str] = []
    for tag in soup.find_all("img"):
        src = tag.get("src") or tag.get("data-src")
        if src:
            images.append(src.strip())

    return {
        "name": name or "Unnamed product",
        "price": price_value,
        "description": description,
        "images": images,
        "category": category,
        "sku": sku,
        "url": url,
    }


__all__ = ["extract_product_data"]
