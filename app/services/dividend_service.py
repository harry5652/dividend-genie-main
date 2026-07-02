from typing import Any

from app.data.dividends import DIVIDEND_DATA


def get_dividend_info(symbol, shares=None):
    if not symbol or not isinstance(symbol, str):
        raise ValueError("Invalid symbol provided")

    symbol = symbol.upper().strip()
    clean = symbol.replace(".NS", "").replace(".BO", "")
    data = DIVIDEND_DATA.get(clean)

    if not data:
        return None

    annual_dividend = data["annual_dividend_per_share"]
    yearly = None
    monthly = None

    if shares is not None:
        yearly = shares * annual_dividend
        monthly = yearly / 12

    return {
        "symbol": clean,
        "annual_dividend_per_share": annual_dividend,
        "yield_percent": data["yield_percent"],
        "shares": shares,
        "yearly": yearly,
        "monthly": monthly,
    }


def calculate_dividend_income(symbol: str, shares: int):
    data = get_dividend_info(symbol, shares=shares)
    if not data:
        return None

    return {
        "yearly": data["yearly"],
        "monthly": data["monthly"],
        "yield_percent": data["yield_percent"],
    }


def format_dividend_message(data: Any, shares: int | None = None):
    if isinstance(data, dict):
        payload = data
        symbol = payload.get("symbol") or "Unknown"
        shares_value = payload.get("shares") if payload.get("shares") is not None else shares
    else:
        payload = get_dividend_info(data, shares=shares)
        symbol = data
        shares_value = shares

    if not payload:
        return f"No dividend data for {symbol}"

    if shares_value is None:
        return (
            f"💰 {symbol} Dividend\n"
            f"Annual dividend/share: ₹{payload['annual_dividend_per_share']:,.2f}\n"
            f"Yield: {payload['yield_percent']}%"
        )

    yearly = payload.get("yearly")
    monthly = payload.get("monthly")

    if yearly is None or monthly is None:
        yearly = shares_value * payload["annual_dividend_per_share"]
        monthly = yearly / 12

    return (
        f"💰 {symbol} Dividend\n"
        f"Shares: {shares_value}\n"
        f"Yearly: ₹{yearly:,.2f}\n"
        f"Monthly: ₹{monthly:,.2f}\n"
        f"Yield: {payload['yield_percent']}%"
    )

