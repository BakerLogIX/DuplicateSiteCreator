"""HTTP request helper with retries, throttling and robots.txt awareness."""
from __future__ import annotations

import time
from typing import Dict, Optional
from urllib.parse import urlparse
from urllib.robotparser import RobotFileParser

import requests
from requests import Response

from core.logging.logger import get_logger

LOGGER = get_logger(__name__)


class RequestManager:
    """Fetch HTML documents with basic politeness safeguards."""

    def __init__(
        self,
        *,
        timeout: int = 8,
        max_retries: int = 2,
        backoff: float = 0.5,
        headers: Optional[Dict[str, str]] = None,
        proxies: Optional[Dict[str, str]] = None,
        respect_robots: bool = True,
        min_interval: float = 1.0,
        user_agent: str = "DuplicateSiteCreatorBot/1.0",
    ) -> None:
        self.timeout = timeout
        self.max_retries = max_retries
        self.backoff = backoff
        self.respect_robots = respect_robots
        self.min_interval = min_interval
        self.session = requests.Session()
        self.session.headers.update(headers or {})
        self.session.headers.setdefault("User-Agent", user_agent)
        self.session.proxies.update(proxies or {})
        self._robots_cache: Dict[str, RobotFileParser] = {}
        self._last_request_time: Dict[str, float] = {}

    def _get_robot_parser(self, url: str) -> RobotFileParser:
        parsed = urlparse(url)
        base = f"{parsed.scheme}://{parsed.netloc}"
        robots_url = f"{base}/robots.txt"
        if robots_url not in self._robots_cache:
            parser = RobotFileParser()
            parser.set_url(robots_url)
            try:
                parser.read()
            except Exception:
                parser = RobotFileParser()  # fallback to allow
                parser.parse([])
            self._robots_cache[robots_url] = parser
        return self._robots_cache[robots_url]

    def _allowed(self, url: str) -> bool:
        if not self.respect_robots:
            return True
        parser = self._get_robot_parser(url)
        try:
            return parser.can_fetch(self.session.headers.get("User-Agent", "*"), url)
        except Exception:
            return True

    def _throttle(self, url: str) -> None:
        if self.min_interval <= 0:
            return
        domain = urlparse(url).netloc
        last = self._last_request_time.get(domain)
        now = time.monotonic()
        if last is not None:
            elapsed = now - last
            if elapsed < self.min_interval:
                time.sleep(self.min_interval - elapsed)
        self._last_request_time[domain] = time.monotonic()

    def fetch(self, url: str) -> Optional[str]:
        """Return HTML content for a URL or None on failure."""

        if not self._allowed(url):
            LOGGER.info("Blocked by robots.txt: %s", url)
            return None

        self._throttle(url)
        attempt = 0
        while attempt <= self.max_retries:
            try:
                response: Response = self.session.get(url, timeout=self.timeout)
                if response.status_code == 200 and "text/html" in response.headers.get(
                    "Content-Type", ""
                ):
                    return response.text
                if response.status_code == 200:
                    return response.text
                LOGGER.debug("Non-200 status %s for %s", response.status_code, url)
            except requests.RequestException as exc:
                LOGGER.debug("Request attempt %s failed for %s: %s", attempt + 1, url, exc)

            attempt += 1
            if attempt <= self.max_retries:
                time.sleep(self.backoff * attempt)
        LOGGER.warning("Failed to fetch %s after %s attempts", url, self.max_retries + 1)
        return None


__all__ = ["RequestManager"]
