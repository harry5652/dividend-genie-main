import yfinance as yf


def get_live_price(symbol: str) -> float | None:
    """
    Fetch live-ish price from Yahoo Finance.
    Works for NSE stocks with .NS suffix.
    """
    try:
        ticker = f"{symbol}.NS"
        data = yf.Ticker(ticker)

        price = data.fast_info.get("last_price")

        if price is None:
            price = data.info.get("regularMarketPrice")

        return float(price) if price else None

    except Exception as e:
        print("Price fetch error:", e)
        return None