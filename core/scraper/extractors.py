"""Data extraction helpers for scraped pages."""
from __future__ import annotations

import re
from decimal import Decimal
from html import unescape
from typing import Dict, List, Optional
from urllib.parse import urljoin

CURRENCY_SYMBOLS = {
    "$": "USD",
    "€": "EUR",
    "£": "GBP",
}


def _clean_text(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None
    cleaned = re.sub(r"<[^>]+>", " ", value)
    stripped = " ".join(unescape(cleaned).split())
    return stripped or None


def _parse_price(raw_price: str) -> Optional[Decimal]:
    price_match = re.search(r"([0-9]+[\.,][0-9]{2})", raw_price)
    if not price_match:
        return None
    normalized = price_match.group(1).replace(",", ".")
    try:
        return Decimal(normalized)
    except Exception:
        return None


def _find_tag_content(html: str, tag: str) -> Optional[str]:
    pattern = re.compile(rf"<{tag}[^>]*>(.*?)</{tag}>", re.I | re.S)
    match = pattern.search(html)
    if not match:
        return None
    return match.group(1)


def extract_product_data(html: str, url: str) -> Dict[str, object]:
    """Extract key product fields from HTML."""

    # Name
    title_content = _find_tag_content(html, "h1") or _find_tag_content(html, "h2")
    name = _clean_text(title_content)

    # Price
    price_candidates: List[str] = []
    for pattern in [
        r"itemprop\s*=\s*\"price\"[^>]*content=\"([^\"]+)\"",
        r"class=\"[^\"]*(?:price|product-price)[^\"]*\"[^>]*>(.*?)</",
    ]:
        for match in re.finditer(pattern, html, re.I | re.S):
            price_candidates.append(match.group(1))
    if not price_candidates:
        price_candidates.append(html)

    price: Optional[Decimal] = None
    currency: Optional[str] = None
    for candidate in price_candidates:
        price = _parse_price(candidate)
        if price is not None:
            for symbol, code in CURRENCY_SYMBOLS.items():
                if symbol in candidate:
                    currency = code
                    break
            break

    if currency is None:
        currency_match = re.search(
            r"itemprop\s*=\s*\"priceCurrency\"[^>]*content=\"([^\"]+)\"", html, re.I
        )
        if currency_match:
            currency = currency_match.group(1)

    # Description
    description_match = re.search(
        r'<[^>]*class="[^"]*description[^"]*"[^>]*>(.*?)</[^>]+>', html, re.I | re.S
    )
    if description_match:
        description = _clean_text(description_match.group(1))
    else:
        description = _clean_text(_find_tag_content(html, "p"))

    # SKU
    sku_match = re.search(
        r'itemprop\s*=\s*"sku"[^>]*content="([^"]+)"', html, re.I
    ) or re.search(r"sku[:\s]*([\w-]+)", html, re.I)
    sku = _clean_text(sku_match.group(1)) if sku_match else None

    # Category
    category = None
    breadcrumb_match = re.search(
        r'<(nav|ol|ul)[^>]*class="[^"]*breadcrumb[^"]*"[^>]*>(.*?)</\1>',
        html,
        re.I | re.S,
    )
    if breadcrumb_match:
        items = re.findall(r"<li[^>]*>(.*?)</li>", breadcrumb_match.group(2), re.I | re.S)
        if items:
            category = _clean_text(items[-1])

    # Images
    images: List[str] = []
    for attr in ["src", "data-src"]:
        for match in re.finditer(rf'<img[^>]*{attr}="([^"]+)"', html, re.I):
            img_url = urljoin(url, match.group(1))
            if img_url not in images:
                images.append(img_url)

    return {
        "name": name,
        "price": price,
        "currency": currency,
        "description": description,
        "category": category,
        "sku": sku,
        "images": images,
    }
