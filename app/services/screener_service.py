"""
Screener.in and StockEdge integration.
- Provides direct page URLs for both platforms.
- Optionally scrapes Screener.in for latest dividend history.
"""
from __future__ import annotations

import logging
import re

try:
    import requests
except ImportError:  # pragma: no cover - optional dependency
    requests = None

try:
    from bs4 import BeautifulSoup
except ImportError:  # pragma: no cover - optional dependency
    BeautifulSoup = None

logger = logging.getLogger(__name__)

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,*/*",
    "Accept-Language": "en-US,en;q=0.9",
}


def _clean(symbol: str) -> str:
    return symbol.upper().replace(".NS", "").replace(".BO", "").strip()


def get_screener_url(symbol: str) -> str:
    return f"https://www.screener.in/company/{_clean(symbol)}/"


def get_stockedge_url(symbol: str) -> str:
    return f"https://web.stockedge.com/share/{_clean(symbol)}"


def get_screener_dividend_history(symbol: str) -> list[dict]:
    """
    Scrape Screener.in for recent dividend history.
    Returns a list of dicts [{date, amount}], or [] on failure.
    """
    if requests is None:
        logger.warning("requests is not available; skipping Screener scrape for %s", symbol)
        return []

    url = get_screener_url(symbol)
    try:
        resp = requests.get(url, headers=_HEADERS, timeout=10)
        if resp.status_code != 200:
            logger.warning("Screener returned HTTP %s for %s", resp.status_code, symbol)
            return []

        if BeautifulSoup is None:
            logger.warning("BeautifulSoup is not available; skipping Screener scrape for %s", symbol)
            return []

        soup = BeautifulSoup(resp.text, "lxml")
        history = []

        # Screener renders dividends inside a section with id or heading "Dividends"
        for section in soup.find_all("section"):
            heading = section.find(["h2", "h3", "h4"])
            if not heading or "dividend" not in heading.get_text(strip=True).lower():
                continue
            table = section.find("table")
            if not table:
                continue
            for row in table.find_all("tr")[1:6]:  # up to 5 most recent rows
                cols = [td.get_text(strip=True) for td in row.find_all("td")]
                if len(cols) >= 2:
                    history.append({"date": cols[0], "amount": cols[1]})
            break  # found the section, stop

        logger.info("Screener history for %s: %d rows", symbol, len(history))
        return history

    except Exception as e:
        logger.warning("Screener scrape failed for %s: %s", symbol, e)
        return []
