from sqlalchemy import select
from app.models.portfolio import Portfolio


class PortfolioRepository:

    def get_user_holdings(self, db, user_id: int):
        return db.execute(
            select(Portfolio).where(Portfolio.user_id == user_id)
        ).scalars().all()

    def get_holding(self, db, user_id: int, symbol: str):
        return db.execute(
            select(Portfolio).where(
                Portfolio.user_id == user_id,
                Portfolio.symbol == symbol
            )
        ).scalar_one_or_none()

    def add(self, db, holding: Portfolio):
        db.add(holding)
        db.flush()
        return holding