"""
User tracking service.
Records every Telegram user who interacts with the bot and logs their commands.
"""
from __future__ import annotations

import logging
from contextlib import contextmanager
from datetime import datetime, timedelta

from sqlalchemy import func, select
from telegram import User
from app.models.user import User, CommandLog
from app.database.session import get_session
from app.repositories.user_repository import UserRepository
from app.repositories.command_log_repository import CommandLogRepository

logger = logging.getLogger(__name__)


@contextmanager
def _session():
    db = get_session()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def track(
    tg_user,
    command: str,
    args: str | None = None,
    response_time_ms: int | None = None,
    success: bool | None = None,
) -> None:

    if tg_user is None:
        logger.warning("track called without user")
        return

    try:
        with _session() as db:
            user_repo = UserRepository()
            log_repo = CommandLogRepository()

            now = datetime.utcnow()

            user = user_repo.get_by_telegram_id(db, tg_user.id)

            if not user:
                user = user_repo.create(db, tg_user)
            else:
                user_repo.update_last_seen(user, now)

            log_repo.add(
                db,
                CommandLog(
                    user_id=user.id,
                    command=command,
                    args=args[:256] if args else None,
                    response_time_ms=response_time_ms,
                    success=success,
                ),
            )
    except Exception as exc: 
        logger.error("tracker.track failed: %s", exc, exc_info=True)


def get_stats() -> dict:
    """Return a summary dict for the /stats command."""
    try:
        with _session() as db:
            now = datetime.utcnow()
            today = now.replace(hour=0, minute=0, second=0, microsecond=0)
            week = today - timedelta(days=7)
            month = today - timedelta(days=30)

            total_users = db.execute(select(func.count()).select_from(User)).scalar()
            active_today = db.execute(
                select(func.count()).select_from(User).where(User.last_seen >= today)
            ).scalar()
            active_week = db.execute(
                select(func.count()).select_from(User).where(User.last_seen >= week)
            ).scalar()
            active_month = db.execute(
                select(func.count()).select_from(User).where(User.last_seen >= month)
            ).scalar()
            total_commands = db.execute(select(func.count()).select_from(CommandLog)).scalar()

            top_cmds = db.execute(
                select(CommandLog.command, func.count().label("cnt"))
                .group_by(CommandLog.command)
                .order_by(func.count().desc())
                .limit(5)
            ).all()

            top_users = db.execute(
                select(
                    User.first_name,
                    User.username,
                    func.count(CommandLog.id).label("commands"),
                )
                .join(CommandLog, CommandLog.user_id == User.id)
                .group_by(User.id, User.first_name, User.username)
                .order_by(func.count(CommandLog.id).desc())
                .limit(5)
            ).all()

        return {
            "total_users": total_users,
            "active_today": active_today,
            "active_week": active_week,
            "active_month": active_month,
            "total_commands": total_commands,
            "top_commands": [{"command": r.command, "count": r.cnt} for r in top_cmds],
            "top_users": [
                {
                    "name": r.first_name or "Unknown",
                    "username": r.username,
                    "commands": r.commands,
                }
                for r in top_users
            ],
        }
    except Exception:
        logger.exception("tracker.get_stats failed")
        return {}

