"""
Fetches corporate action data from NSE India's API.
Supports dividends, bonus issues, and stock splits.
"""
from __future__ import annotations

import logging
import re
import time
from datetime import datetime, timedelta, date

try:
    import requests
except ImportError:  # pragma: no cover - optional dependency
    requests = None

logger = logging.getLogger(__name__)

NSE_BASE = "https://www.nseindia.com"
_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://www.nseindia.com/",
}

_session: requests.Session | None = None
_session_ts: float = 0
_SESSION_TTL = 300  # seconds before refreshing cookies


def _get_session():
    global _session, _session_ts
    if requests is None:
        logger.warning("requests is not available; skipping NSE session initialization")
        return None

    if _session is None or (time.time() - _session_ts) > _SESSION_TTL:
        s = requests.Session()
        s.headers.update(_HEADERS)
        try:
            s.get(NSE_BASE, timeout=10)
            time.sleep(0.5)  # let cookies settle
        except Exception as e:
            logger.warning("NSE session init error: %s", e)
        _session = s
        _session_ts = time.time()
    return _session


def _parse_amount(subject: str) -> float | None:
    """Extract ₹ amount from strings like 'Dividend - Rs 8.50 Per Share'."""
    patterns = [
        r"rs\.?\s*([\d,]+\.?\d*)\s*per\s*share",
        r"₹\s*([\d,]+\.?\d*)\s*per\s*share",
        r"dividend[^\d]*([\d,]+\.?\d*)\s*per\s*share",
        r"rs\.?\s*([\d,]+\.?\d*)",
    ]
    s = subject.lower()
    for pat in patterns:
        m = re.search(pat, s)
        if m:
            try:
                return float(m.group(1).replace(",", ""))
            except ValueError:
                pass
    return None


def _parse_date(date_str: str) -> date | None:
    for fmt in ("%d-%b-%Y", "%d-%b-%y", "%d/%m/%Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(date_str.strip(), fmt).date()
        except ValueError:
            continue
    return None


def _detect_type(subject: str) -> str:
    """Classify a corporate action subject as DIVIDEND, BONUS, SPLIT, or OTHER."""
    s = subject.upper()
    if "DIVIDEND" in s:
        return "DIVIDEND"
    if "BONUS" in s:
        return "BONUS"
    if "SPLIT" in s or "SUB-DIVISION" in s or "SUB DIVISION" in s or "SUBDIVISION" in s:
        return "SPLIT"
    return "OTHER"


def _parse_ratio(subject: str) -> str | None:
    """Extract a ratio like '1:1' or '2:1' from bonus/split subjects."""
    m = re.search(r"(\d+)\s*:\s*(\d+)", subject)
    if m:
        return f"{m.group(1)}:{m.group(2)}"
    return None


def _parse_split_faces(subject: str) -> str | None:
    """
    Extract face-value change from split subjects like
    'Sub-Division from Rs 10/- to Rs 5/-' → 'Rs 10 → Rs 5'
    """
    m = re.search(r"rs\.?\s*([\d,]+\.?\d*).*?to\s+rs\.?\s*([\d,]+\.?\d*)", subject.lower())
    if m:
        return f"₹{m.group(1)} → ₹{m.group(2)}"
    return None


def _fetch_actions() -> list[dict]:
    session = _get_session()
    if session is None:
        return []
    url = f"{NSE_BASE}/api/corporates-corporateActions?index=equities"
    try:
        resp = session.get(url, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        return data if isinstance(data, list) else []
    except Exception as e:
        logger.error("NSE corporate actions fetch failed: %s", e)
        return []


def get_upcoming_corporate_actions(days: int = 30) -> list[dict]:
    """
    Return upcoming corporate actions (dividends, bonus, splits) with ex-date
    within the next `days` days, sorted by ex-date then type.
    """
    actions = _fetch_actions()
    today  = datetime.now().date()
    cutoff = today + timedelta(days=days)

    results = []
    for item in actions:
        subject = item.get("subject") or ""
        action_type = _detect_type(subject)
        if action_type == "OTHER":
            continue

        ex_date = _parse_date(item.get("exDate") or "")
        if not ex_date or not (today <= ex_date <= cutoff):
            continue

        record_date = _parse_date(item.get("recDate") or "")

        entry = {
            "type":        action_type,
            "symbol":      item.get("symbol", ""),
            "company":     item.get("comp", ""),
            "series":      item.get("series", "EQ"),
            "ex_date":     ex_date,
            "record_date": record_date,
            "subject":     subject,
        }

        if action_type == "DIVIDEND":
            entry["amount"] = _parse_amount(subject)
        elif action_type == "BONUS":
            entry["ratio"] = _parse_ratio(subject)
        elif action_type == "SPLIT":
            entry["ratio"]       = _parse_ratio(subject)
            entry["face_change"] = _parse_split_faces(subject)

        results.append(entry)

    return sorted(results, key=lambda x: (x["ex_date"], x["type"]))


def get_upcoming_dividends(days: int = 30) -> list[dict]:
    """Backward-compatible: return only dividend events."""
    return [
        a for a in get_upcoming_corporate_actions(days)
        if a["type"] == "DIVIDEND"
    ]


def _fetch_actions_range(from_date: date, to_date: date) -> list[dict]:
    """Fetch corporate actions for a specific date range."""
    session = _get_session()
    if session is None:
        return []
    fmt = "%d-%m-%Y"
    url = (
        f"{NSE_BASE}/api/corporates-corporateActions?index=equities"
        f"&from_date={from_date.strftime(fmt)}&to_date={to_date.strftime(fmt)}"
    )
    try:
        resp = session.get(url, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        return data if isinstance(data, list) else []
    except Exception as e:
        logger.error("NSE ranged fetch failed (%s→%s): %s", from_date, to_date, e)
        return []


def _symbol_history(symbol: str, action_type: str, years: int = 10) -> list[dict]:
    """Return historical corporate actions of a given type for a symbol."""
    bare  = symbol.upper().replace(".NS", "").replace(".BO", "").strip()
    today = datetime.now().date()
    start = today.replace(year=today.year - years)

    # NSE API caps single ranges; chunk by year
    all_actions: list[dict] = []
    chunk_start = start
    while chunk_start < today:
        chunk_end = min(chunk_start.replace(year=chunk_start.year + 1), today)
        all_actions += _fetch_actions_range(chunk_start, chunk_end)
        chunk_start = chunk_end

    results = []
    for item in all_actions:
        if item.get("symbol", "").upper() != bare:
            continue
        subject = item.get("subject") or ""
        if _detect_type(subject) != action_type:
            continue

        ex_date     = _parse_date(item.get("exDate") or "")
        record_date = _parse_date(item.get("recDate") or "")
        payout_date = _parse_date(item.get("setPayDt") or "")

        entry = {
            "symbol":      bare,
            "company":     item.get("comp", ""),
            "ex_date":     ex_date,
            "record_date": record_date,
            "payout_date": payout_date,
            "subject":     subject,
        }
        if action_type == "BONUS":
            entry["ratio"] = _parse_ratio(subject)
        elif action_type == "SPLIT":
            entry["ratio"]       = _parse_ratio(subject)
            entry["face_change"] = _parse_split_faces(subject)
        elif action_type == "DIVIDEND":
            entry["amount"] = _parse_amount(subject)

        results.append(entry)

    # Deduplicate by ex_date + subject
    seen = set()
    unique = []
    for r in results:
        key = (r.get("ex_date"), r["subject"])
        if key not in seen:
            seen.add(key)
            unique.append(r)

    return sorted(unique, key=lambda x: x["ex_date"] or date.min, reverse=True)


def get_symbol_bonus_history(symbol: str) -> list[dict]:
    return _symbol_history(symbol, "BONUS")


def get_symbol_split_history(symbol: str) -> list[dict]:
    return _symbol_history(symbol, "SPLIT")


def get_nse_dividend_detail(symbol: str) -> dict | None:
    """
    Return the most relevant (upcoming or latest past) dividend detail for `symbol`.
    Returns dict with ex_date, record_date, payout_date, amount; or None if not found.
    """
    bare = symbol.upper().replace(".NS", "").replace(".BO", "").strip()
    actions = _fetch_actions()
    today = datetime.now().date()

    candidates = []
    for item in actions:
        if item.get("symbol", "").upper() != bare:
            continue
        if "DIVIDEND" not in (item.get("subject") or "").upper():
            continue
        ex_date = _parse_date(item.get("exDate") or "")
        candidates.append((ex_date, item))

    if not candidates:
        return None

    upcoming = [(d, i) for d, i in candidates if d and d >= today]
    past     = [(d, i) for d, i in candidates if d and d <  today]

    chosen_date, chosen = (
        min(upcoming, key=lambda x: x[0]) if upcoming
        else max(past, key=lambda x: x[0])
    )

    return {
        "ex_date":     chosen_date,
        "record_date": _parse_date(chosen.get("recDate") or ""),
        "payout_date": _parse_date(chosen.get("setPayDt") or ""),
        "amount":      _parse_amount(chosen.get("subject") or ""),
        "subject":     chosen.get("subject", ""),
    }
