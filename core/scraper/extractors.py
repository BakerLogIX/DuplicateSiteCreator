"""Functions to extract product data from HTML."""
from typing import Dict, Optional

from bs4 import BeautifulSoup

from core.scraper.detectors import is_product_page


def extract_product_data(html: str, url: str) -> Optional[Dict[str, object]]:
    soup = BeautifulSoup(html, "lxml")
    if not is_product_page(html):
        return None

    title = soup.find("h1") or soup.find("title")
    name = title.get_text(strip=True) if title else url
    price_tag = soup.find(class_=lambda value: value and "price" in value)
    price_text = price_tag.get_text(strip=True) if price_tag else "0"
    description_tag = soup.find("p")
    description = description_tag.get_text(strip=True) if description_tag else ""
    images = [img.get("src") for img in soup.find_all("img") if img.get("src")]

    return {
        "name": name,
        "description": description,
        "price": _parse_price(price_text),
        "currency": "USD",
        "images": images,
        "source_url": url,
    }


def _parse_price(value: str) -> float:
    digits = "".join(ch for ch in value if ch.isdigit() or ch == ".")
    try:
        return float(digits)
    except ValueError:
        return 0.0
