"""Simple HTTP request manager with retry support."""
from typing import Optional

import requests
from requests import Response

from core.logging.logger import get_logger

logger = get_logger(__name__)


class RequestManager:
    """Lightweight wrapper around requests to fetch HTML documents."""

    def __init__(self, timeout: int = 10, max_retries: int = 3, user_agent: Optional[str] = None):
        self.timeout = timeout
        self.max_retries = max_retries
        self.headers = {"User-Agent": user_agent or "DuplicateSiteCreator/0.1"}

    def fetch(self, url: str) -> Optional[str]:
        for attempt in range(1, self.max_retries + 1):
            try:
                response: Response = requests.get(url, headers=self.headers, timeout=self.timeout)
                response.raise_for_status()
                return response.text
            except requests.RequestException as exc:
                logger.warning("Attempt %s failed for %s: %s", attempt, url, exc)
        logger.error("Failed to fetch %s after %s attempts", url, self.max_retries)
        return None
