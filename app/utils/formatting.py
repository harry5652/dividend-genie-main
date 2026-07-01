"""
Shared formatting helpers used across services and commands.
"""
from __future__ import annotations

from datetime import date, datetime


def fmt_date(value: date | datetime | None, fmt: str = "%d %b %Y") -> str:
    """Return a human-readable date string, or 'N/A' if the value is None."""
    if value is None:
        return "N/A"
    return value.strftime(fmt)


def fmt_currency(amount: float | None, symbol: str = "₹") -> str:
    """Format a monetary amount with a currency symbol."""
    if amount is None:
        return "N/A"
    return f"{symbol}{amount:,.2f}"


def fmt_pct(value: float | None, decimals: int = 2) -> str:
    """Format a percentage value."""
    if value is None:
        return "N/A"
    return f"{value:.{decimals}f}%"
