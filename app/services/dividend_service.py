from app.data.dividends import DIVIDEND_DATA


def get_dividend_info(symbol: str):
    clean = symbol.upper().replace(".NS", "").strip()
    return DIVIDEND_DATA.get(clean)


def calculate_dividend_income(symbol: str, shares: int):
    data = get_dividend_info(symbol)
    if not data:
        return None

    yearly = shares * data["annual_dividend_per_share"]
    monthly = yearly / 12
    yield_percent = data["yield_percent"]

    return {
        "yearly": yearly,
        "monthly": monthly,
        "yield_percent": yield_percent
    }

def format_dividend_message(symbol: str, shares: int):
    data = get_dividend_info(symbol)

    if not data:
        return f"No dividend data for {symbol}"

    yearly = shares * data["annual_dividend_per_share"]
    monthly = yearly / 12

    return (
        f"💰 {symbol} Dividend\n"
        f"Shares: {shares}\n"
        f"Yearly: ₹{yearly:,.2f}\n"
        f"Monthly: ₹{monthly:,.2f}\n"
        f"Yield: {data['yield_percent']}%"
    )

