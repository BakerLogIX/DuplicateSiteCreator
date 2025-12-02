"""HTTP request manager for controlled scraping."""
from __future__ import annotations

import time
from typing import Dict, Optional
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, build_opener, install_opener
from urllib.robotparser import RobotFileParser


class RequestManager:
    """Manage HTTP requests with throttling, retries and robots.txt respect."""

    def __init__(
        self,
        user_agent: str = "DuplicateSiteCreatorBot/1.0",
        timeout: float = 10.0,
        max_retries: int = 2,
        backoff_factor: float = 0.5,
        throttle_seconds: float = 1.0,
        proxies: Optional[Dict[str, str]] = None,
    ) -> None:
        self.user_agent = user_agent
        self.timeout = timeout
        self.max_retries = max_retries
        self.backoff_factor = backoff_factor
        self.throttle_seconds = throttle_seconds
        self.proxies = proxies or {}
        self._last_request_time: Optional[float] = None
        self._robot_parsers: Dict[str, RobotFileParser] = {}

        self.opener = build_opener()
        if self.proxies:
            self.opener.add_handler(
                self.opener.handler_classes["ProxyHandler"](self.proxies)  # type: ignore[index]
            )
        install_opener(self.opener)

    def _sleep_for_throttle(self) -> None:
        if self._last_request_time is None:
            return
        elapsed = time.time() - self._last_request_time
        remaining = self.throttle_seconds - elapsed
        if remaining > 0:
            time.sleep(remaining)

    def _allowed_by_robots(self, url: str) -> bool:
        parsed = urlparse(url)
        if parsed.scheme not in {"http", "https"}:
            return True

        base = f"{parsed.scheme}://{parsed.netloc}"
        if base not in self._robot_parsers:
            robots_url = f"{base}/robots.txt"
            parser = RobotFileParser()
            try:
                parser.set_url(robots_url)
                parser.read()
            except Exception:
                parser.disallow_all = False
            self._robot_parsers[base] = parser
        parser = self._robot_parsers[base]
        return parser.can_fetch(self.user_agent, url)

    def fetch(self, url: str) -> str:
        """Fetch the content at ``url`` respecting throttling and robots.txt."""

        if not self._allowed_by_robots(url):
            raise PermissionError(f"Robots.txt forbids fetching {url}")

        last_exception: Optional[Exception] = None
        for attempt in range(self.max_retries + 1):
            try:
                self._sleep_for_throttle()
                request = Request(url, headers={"User-Agent": self.user_agent})
                with self.opener.open(request, timeout=self.timeout) as response:
                    status = getattr(response, "status", response.getcode())
                    if status and status >= 400:
                        raise HTTPError(url, status, "HTTP error", hdrs=None, fp=None)
                    content_bytes = response.read()
                    self._last_request_time = time.time()
                    encoding = response.headers.get_content_charset() or "utf-8"
                    return content_bytes.decode(encoding, errors="replace")
            except (HTTPError, URLError) as exc:  # pragma: no cover - network paths
                last_exception = exc
                time.sleep(self.backoff_factor * (attempt + 1))
        if last_exception:
            raise last_exception
        raise URLError("Request failed for unknown reasons")
