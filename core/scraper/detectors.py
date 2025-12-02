"""Heuristics to identify product pages."""
from bs4 import BeautifulSoup


PRICE_HINTS = ["price", "sale", "amount", "cost"]
ADD_TO_CART_HINTS = ["add to cart", "add-to-cart", "cart"]


def is_product_page(html: str) -> bool:
    soup = BeautifulSoup(html, "lxml")
    text = soup.get_text(" ", strip=True).lower()
    has_price_hint = any(hint in text for hint in PRICE_HINTS)
    has_button = any(hint in text for hint in ADD_TO_CART_HINTS)
    return has_price_hint and has_button
