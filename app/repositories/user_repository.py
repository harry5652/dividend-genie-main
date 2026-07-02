from sqlalchemy import select
from app.models.user import CommandLog
from app.models.user import User

class UserRepository:

    def get_by_telegram_id(self, db, telegram_id: int):
        return db.execute(
            select(User).where(User.telegram_id == telegram_id)
        ).scalar_one_or_none()

    def create(self, db, tg_user):
        user = User(
            telegram_id=tg_user.id,
            username=tg_user.username,
            first_name=tg_user.first_name,
            last_name=tg_user.last_name,
        )
        db.add(user)
        db.flush()
        return user

    def update_last_seen(self, user, now):
        user.last_seen = now
        return user