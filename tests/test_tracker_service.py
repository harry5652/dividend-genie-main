from types import SimpleNamespace

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.models.user import Base, CommandLog, User
from app.services import tracker_service


def test_track_persists_command_log_for_new_user(monkeypatch):
    engine = create_engine("sqlite:///:memory:")
    TestingSession = sessionmaker(bind=engine, autocommit=False, autoflush=False)
    Base.metadata.create_all(bind=engine)

    monkeypatch.setattr(tracker_service, "SessionLocal", TestingSession)

    tg_user = SimpleNamespace(
        id=101,
        username="alice",
        first_name="Alice",
        last_name="Smith",
    )

    tracker_service.track(tg_user, "start")

    with TestingSession() as db:
        user = db.query(User).filter(User.telegram_id == tg_user.id).one()
        command_logs = db.query(CommandLog).filter(CommandLog.user_id == user.id).all()

    assert user.id is not None
    assert len(command_logs) == 1
    assert command_logs[0].command == "start"
