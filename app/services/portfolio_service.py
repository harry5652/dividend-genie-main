"""
Portfolio service helpers (production stable version)
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from sqlalchemy import select

from app.database.session import get_session
from app.models.portfolio import Portfolio
from app.models.user import User


@dataclass(frozen=True)
class HoldingResult:
    symbol: str
    shares: int
    avg_price: float
    added_shares: int
    added_price: float
    total_invested: float
    is_new: bool


# ─────────────────────────────────────────────────────────────
# ADD / UPDATE HOLDING
# ─────────────────────────────────────────────────────────────

def add_holding(tg_user, symbol: str, shares: int, price: float) -> HoldingResult:
    symbol = symbol.upper().strip()

    if not symbol:
        raise ValueError("Symbol is required.")
    if shares <= 0:
        raise ValueError("Shares must be positive.")
    if price <= 0:
        raise ValueError("Price must be positive.")

    with get_session() as db:
        now = datetime.now(timezone.utc)

        # Get or create user
        user = db.execute(
            select(User).where(User.telegram_id == tg_user.id)
        ).scalar_one_or_none()

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
            db.flush()  # IMPORTANT: ensures user.id exists
        else:
            user.username = tg_user.username
            user.first_name = tg_user.first_name
            user.last_name = tg_user.last_name
            user.last_seen = now

        # Get holding
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

        db.flush()

        return HoldingResult(
            symbol=holding.symbol,
            shares=holding.shares,
            avg_price=holding.avg_price,
            added_shares=shares,
            added_price=price,
            total_invested=holding.shares * holding.avg_price,
            is_new=is_new,
        )


# ─────────────────────────────────────────────────────────────
# GET HOLDINGS
# ─────────────────────────────────────────────────────────────

def get_user_holdings(telegram_id: int):
    with get_session() as db:
        user = db.execute(
            select(User).where(User.telegram_id == telegram_id)
        ).scalar_one_or_none()

        if not user:
            return []

        return db.execute(
            select(Portfolio)
            .where(Portfolio.user_id == user.id)
            .order_by(Portfolio.symbol)
        ).scalars().all()


# ─────────────────────────────────────────────────────────────
# ALL USERS WITH HOLDINGS
# ─────────────────────────────────────────────────────────────

def get_all_users_with_holdings():
    with get_session() as db:
        users = db.execute(select(User)).scalars().all()

        result = []

        for user in users:
            holdings = db.execute(
                select(Portfolio).where(Portfolio.user_id == user.id)
            ).scalars().all()

            if holdings:
                result.append((user, holdings))

        return result