"""Utilities for working with scraped links."""
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup


def normalize_url(href: str, base_url: str) -> str:
    return urljoin(base_url, href)


def is_same_domain(url: str, base_domain: str) -> bool:
    parsed = urlparse(url)
    return parsed.netloc == base_domain


def extract_links(html: str, base_url: str) -> list[str]:
    soup = BeautifulSoup(html, "lxml")
    base_domain = urlparse(base_url).netloc
    links: list[str] = []
    for anchor in soup.find_all("a", href=True):
        normalized = normalize_url(anchor["href"], base_url)
        if is_same_domain(normalized, base_domain):
            links.append(normalized)
    return links
