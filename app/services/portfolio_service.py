"""
Portfolio service helpers.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from sqlalchemy import select

from app.database.session import get_session
from app.models.portfolio import Portfolio


@dataclass(frozen=True)
class HoldingResult:
    symbol: str
    shares: int
    avg_price: float
    added_shares: int
    added_price: float
    total_invested: float
    is_new: bool


def add_holding(tg_user, symbol: str, shares: int, price: float) -> HoldingResult:
    """Create or update a user's holding using weighted average price."""
    symbol = symbol.upper().strip()
    if not symbol:
        raise ValueError("Symbol is required.")
    if shares <= 0:
        raise ValueError("Shares must be a positive whole number.")
    if price <= 0:
        raise ValueError("Price must be a positive number.")

    db = get_session()
    try:
        user = db.execute(
            select(User).where(User.telegram_id == tg_user.id)
        ).scalar_one_or_none()

        now = datetime.now(timezone.utc)
        if user is None:
            user = User(
                telegram_id=tg_user.id,
                username=tg_user.username,
                first_name=tg_user.first_name,
                last_name=tg_user.last_name,
                joined_at=now,
                last_seen=now,
            )
            db.add(user)
            db.flush()
        else:
            user.username = tg_user.username
            user.first_name = tg_user.first_name
            user.last_name = tg_user.last_name
            user.last_seen = now

        holding = db.execute(
            select(Portfolio).where(
                Portfolio.user_id == user.id,
                Portfolio.symbol == symbol,
            )
        ).scalar_one_or_none()

        is_new = holding is None
        if holding is None:
            holding = Portfolio(
                user_id=user.id,
                symbol=symbol,
                shares=shares,
                avg_price=price,
            )
            db.add(holding)
        else:
            current_value = holding.shares * holding.avg_price
            added_value = shares * price
            total_shares = holding.shares + shares
            holding.shares = total_shares
            holding.avg_price = (current_value + added_value) / total_shares

        db.commit()
        db.refresh(holding)

        return HoldingResult(
            symbol=holding.symbol,
            shares=holding.shares,
            avg_price=holding.avg_price,
            added_shares=shares,
            added_price=price,
            total_invested=holding.shares * holding.avg_price,
            is_new=is_new,
        )
    finally:
        db.close()


def get_user_holdings(telegram_id: int):
    db = get_session()
    try:
        user = db.execute(select(User).where(User.telegram_id == telegram_id)).scalar_one_or_none()
        if user is None:
            return []

        return db.execute(
            select(Portfolio).where(Portfolio.user_id == user.id).order_by(Portfolio.symbol)
        ).scalars().all()
    finally:
        db.close()
    
    
def get_all_users_with_holdings():
    db = get_session()
    try:
        users = db.query(User).all()

        result = []

        for user in users:
            holdings = db.query(Portfolio).filter_by(user_id=user.id).all()
            if holdings:
                result.append((user, holdings))

        return result
    finally:
        db.close()