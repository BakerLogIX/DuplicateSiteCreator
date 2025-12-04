"""Utilities for normalising and extracting links during scraping."""
from __future__ import annotations

from typing import List, Set
from urllib.parse import urljoin, urlparse, urlunparse

from bs4 import BeautifulSoup


def _strip_fragment(url: str) -> str:
    parsed = urlparse(url)
    cleaned = parsed._replace(fragment="")
    return urlunparse(cleaned)


def normalize_url(href: str, base_url: str) -> str | None:
    """Resolve an href against a base URL and strip fragments."""

    if not href:
        return None
    absolute = urljoin(base_url, href)
    parsed = urlparse(absolute)
    if parsed.scheme not in {"http", "https"}:
        return None
    return _strip_fragment(absolute.rstrip("/"))


def _normalize_domain(domain: str) -> str:
    domain = domain.lower()
    return domain[4:] if domain.startswith("www.") else domain


def is_same_domain(url: str, base_domain: str) -> bool:
    parsed = urlparse(url)
    if not parsed.netloc:
        return False
    return _normalize_domain(parsed.netloc) == _normalize_domain(base_domain)


def extract_links(html: str, base_url: str) -> List[str]:
    """Extract and normalize anchor links from HTML."""

    soup = BeautifulSoup(html, "html.parser")
    links: Set[str] = set()
    for tag in soup.find_all("a", href=True):
        normalized = normalize_url(tag.get("href"), base_url)
        if normalized:
            links.add(normalized)
    return sorted(links)


__all__ = ["normalize_url", "is_same_domain", "extract_links"]
