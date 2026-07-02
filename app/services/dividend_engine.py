# app/services/dividend_engine.py

from dataclasses import dataclass

@dataclass
class DividendResult:
    symbol: str
    yearly_dividend: float
    monthly_dividend: float
    yield_percent: float


# Temporary dividend database (we will later replace with API)
DIVIDEND_DB = {
    "ITC": 15.0,      # ₹ per share per year (approx historical avg)
    "TCS": 115.0,
    "INFY": 32.0,
    "HDFC": 19.0,
    "POWERGRID": 16.0,
}

def calculate_dividend(symbol: str, shares: int, avg_price: float):
    symbol = symbol.upper()

    dividend_per_share = DIVIDEND_DB.get(symbol, 0.0)

    yearly_income = dividend_per_share * shares
    monthly_income = yearly_income / 12

    yield_percent = (
        (dividend_per_share / avg_price) * 100
        if avg_price > 0 else 0
    )

    return DividendResult(
        symbol=symbol,
        yearly_dividend=round(yearly_income, 2),
        monthly_dividend=round(monthly_income, 2),
        yield_percent=round(yield_percent, 2),
    )

def calculate_portfolio_dividends(holdings: list):
    """
    holdings = [
        {"symbol": "ITC", "shares": 20, "avg_price": 100},
        {"symbol": "TCS", "shares": 5, "avg_price": 3500},
    ]
    """

    results = []
    total_yearly = 0.0

    for h in holdings:
        res = calculate_dividend(h["symbol"], h["shares"], h["avg_price"])
        results.append(res)
        total_yearly += res.yearly_dividend

    return {
        "stocks": results,
        "total_yearly": round(total_yearly, 2),
        "total_monthly": round(total_yearly / 12, 2),
    }

