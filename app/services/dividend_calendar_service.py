from datetime import datetime
from app.data.dividend_calendar import DIVIDEND_CALENDAR


def get_upcoming_events(symbol: str):
    symbol = symbol.upper().replace(".NS", "").strip()
    return DIVIDEND_CALENDAR.get(symbol, [])


def get_next_event(symbol: str):
    events = get_upcoming_events(symbol)

    if not events:
        return None

    today = datetime.utcnow().date()

    upcoming = []
    for e in events:
        ex_date = datetime.strptime(e["ex_date"], "%Y-%m-%d").date()
        if ex_date >= today:
            upcoming.append(e)

    return sorted(upcoming, key=lambda x: x["ex_date"])[0] if upcoming else None