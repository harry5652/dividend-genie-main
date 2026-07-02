from datetime import datetime, timezone

from app.database.db import get_db
from app.models.portfolio import Portfolio

def save_user(tg_user):
    with get_db() as db:
        user = db.query(User).filter(User.telegram_id == tg_user.id).first()

        if user is None:
            user = User(
                telegram_id=tg_user.id,
                username=tg_user.username,
                first_name=tg_user.first_name,
                last_name=tg_user.last_name,
            )
            db.add(user)
        else:
            user.username = tg_user.username
            user.first_name = tg_user.first_name
            user.last_name = tg_user.last_name
            user.last_seen = datetime.now(timezone.utc)

