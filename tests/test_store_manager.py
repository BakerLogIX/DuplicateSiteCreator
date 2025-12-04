from typing import Generator

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from core.db.base import Base
from core.store_manager import StoreManager


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


def test_store_manager_create_and_switch(db_session: Session) -> None:
    manager = StoreManager(db_session)

    first = manager.create_store(name="First Store", theme="default")
    second = manager.create_store(name="Second Store", payment_provider="stripe")

    assert manager.get_current_store_id() == second.id
    assert [s.name for s in manager.list_stores()] == ["First Store", "Second Store"]

    manager.set_current_store(first.id)
    assert manager.get_current_store().id == first.id

    ensured = manager.ensure_store("First Store")
    assert ensured.id == first.id

    with pytest.raises(ValueError):
        manager.set_current_store(999)
