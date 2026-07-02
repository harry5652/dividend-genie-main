from app.models.user import CommandLog


class CommandLogRepository:

    def add(self, db, log: CommandLog):
        db.add(log)

    def count_total(self, db):
        return db.query(CommandLog).count()