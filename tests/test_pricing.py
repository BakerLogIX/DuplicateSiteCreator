from decimal import Decimal
from typing import Generator

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from core.db.base import Base
from core.db.repositories import ProductRepository, StoreRepository
from core.pricing.demand_scoring import compute_demand_score
from core.pricing.engine import run_pricing
from core.pricing.rules import DemandRule, MarginRule


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


def test_compute_demand_score_accounts_for_price_and_category() -> None:
    product = type(
        "ProductStub",
        (),
        {"price": Decimal("50"), "category": "Footwear"},
    )()
    high_price_product = type(
        "ProductStub",
        (),
        {"price": Decimal("200"), "category": "Home"},
    )()

    rules = DemandRule(
        base_weight=0.4,
        price_weight=0.4,
        category_weight=0.2,
        price_anchor=100,
        category_multipliers={"footwear": 1.0},
    )

    assert compute_demand_score(product, rules) == pytest.approx(0.8, rel=1e-3)
    assert compute_demand_score(high_price_product, rules) == pytest.approx(0.4, rel=1e-3)


def test_run_pricing_applies_margin_rules(db_session: Session) -> None:
    store_repo = StoreRepository(db_session)
    product_repo = ProductRepository(db_session)

    store = store_repo.create(name="Demo Store", theme="default", payment_provider=None)
    footwear = product_repo.create(
        store_id=store.id,
        name="Trail Runner",
        price=Decimal("50.00"),
        currency="USD",
        category="Footwear",
    )
    accessory = product_repo.create(
        store_id=store.id,
        name="Hydration Pack",
        price=Decimal("150.00"),
        currency="USD",
        category=None,
    )

    demand_rule = DemandRule(
        base_weight=0.4,
        price_weight=0.4,
        category_weight=0.2,
        price_anchor=100,
        category_multipliers={"footwear": 1.0},
    )
    margin_rules = [
        MarginRule(min_margin=0.2, max_margin=0.5, category="Footwear"),
        MarginRule(min_margin=0.1, max_margin=0.3),
    ]

    updated = run_pricing(
        store.id,
        db=db_session,
        margin_rules=margin_rules,
        demand_rule=demand_rule,
    )

    assert {p.id for p in updated} == {footwear.id, accessory.id}

    updated_footwear = product_repo.get_by_id(footwear.id)
    updated_accessory = product_repo.get_by_id(accessory.id)

    assert updated_footwear.price == Decimal("72.00")
    assert updated_accessory.price == Decimal("177.00")
