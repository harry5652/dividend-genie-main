from types import SimpleNamespace

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database.db import Base
from app.models import Portfolio, User  # noqa: F401
from app.services import portfolio_service
from app.services.portfolio_service import add_holding


def test_add_holding_creates_and_updates_weighted_average(monkeypatch):
    engine = create_engine("sqlite:///:memory:")
    TestingSession = sessionmaker(bind=engine, autocommit=False, autoflush=False)
    Base.metadata.create_all(bind=engine)
    monkeypatch.setattr(portfolio_service, "SessionLocal", TestingSession)

    tg_user = SimpleNamespace(
        id=123,
        username="sree",
        first_name="Sree",
        last_name=None,
    )

    first = add_holding(tg_user, "ITC", 25, 420)
    assert first.is_new is True
    assert first.shares == 25
    assert first.avg_price == 420

    second = add_holding(tg_user, "itc", 25, 500)
    assert second.is_new is False
    assert second.shares == 50
    assert second.avg_price == 460
