"""Compliance safeguards tests."""
from __future__ import annotations

from typing import Generator

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from core.db.base import Base
from core.scraper.request_manager import RequestManager


@pytest.fixture()
def db_session() -> Generator[Session, None, None]:
    engine = create_engine("sqlite:///:memory:")
    TestingSessionLocal = sessionmaker(bind=engine)
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


def test_request_manager_blocks_disallowed_urls(monkeypatch) -> None:
    """Robots disallow should short-circuit fetch attempts."""

    rm = RequestManager(respect_robots=True, min_interval=0)
    calls = {"allowed": 0, "get": 0}

    def fake_allowed(url: str) -> bool:
        calls["allowed"] += 1
        return False

    def fake_get(url, timeout=None):
        calls["get"] += 1
        raise AssertionError("Should not call requests.get when disallowed")

    monkeypatch.setattr(rm, "_allowed", fake_allowed)
    monkeypatch.setattr(rm.session, "get", fake_get)

    assert rm.fetch("https://example.com/blocked") is None
    assert calls["allowed"] == 1
    assert calls["get"] == 0
