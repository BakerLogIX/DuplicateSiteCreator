"""Utilities for working with links during scraping."""
from __future__ import annotations

from html.parser import HTMLParser
from typing import List, Optional
from urllib.parse import urljoin, urlparse, urlunparse


class _LinkCollector(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.links: List[str] = []

    def handle_starttag(self, tag: str, attrs) -> None:  # type: ignore[override]
        if tag.lower() != "a":
            return
        href = dict(attrs).get("href")
        if href:
            self.links.append(href)


def normalize_url(href: str, base_url: str) -> Optional[str]:
    """Convert a raw href into an absolute, normalized URL."""

    if not href or href.startswith(("javascript:", "mailto:", "tel:")):
        return None

    absolute = urljoin(base_url, href)
    parsed = urlparse(absolute)
    if not parsed.scheme:
        return None

    normalized = parsed._replace(fragment="")
    return urlunparse(normalized)


def is_same_domain(url: str, base_domain: str) -> bool:
    """Return True if ``url`` belongs to ``base_domain`` ignoring ``www``."""

    parsed = urlparse(url)
    host = parsed.netloc.split(":")[0]
    normalized_host = host[4:] if host.startswith("www.") else host
    normalized_base = base_domain[4:] if base_domain.startswith("www.") else base_domain
    return normalized_host == normalized_base


def extract_links(html: str, base_url: str) -> List[str]:
    """Extract and normalize anchor links from HTML."""

    parser = _LinkCollector()
    parser.feed(html)
    base_domain = urlparse(base_url).netloc

    links: List[str] = []
    seen = set()
    for href in parser.links:
        normalized = normalize_url(href, base_url)
        if not normalized:
            continue
        if not is_same_domain(normalized, base_domain):
            continue
        if normalized in seen:
            continue
        seen.add(normalized)
        links.append(normalized)
    return links
