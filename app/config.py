"""
Application configuration.
Loads settings from environment variables / .env file.
"""
from __future__ import annotations

from email import errors
import logging
import os

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover - optional dependency
    def load_dotenv() -> bool:
        return False

load_dotenv()

logger = logging.getLogger(__name__)


def _parse_admin_id() -> int:
    """
    Parse ADMIN_TELEGRAM_ID from the environment.
    Accepts a plain integer string ("123456789").
    Returns 0 (admin disabled) if the value is missing or non-numeric.
    """
    raw = os.getenv("ADMIN_TELEGRAM_ID", "").strip().lstrip("@")
    if not raw:
        return 0
    try:
        return int(raw)
    except ValueError:
        logger.warning(
            "ADMIN_TELEGRAM_ID=%r is not a numeric Telegram user ID — "
            "admin access disabled. Set it to your numeric ID (e.g. 123456789).",
            raw,
        )
        return 0


class Config:
    def __init__(self) -> None:
        self.APP_ENV: str = os.getenv("APP_ENV", "development")
        self.DEBUG: bool = self.APP_ENV == "development"
        self.DATABASE_URL: str = os.getenv(
            "DATABASE_URL", "sqlite:///dividend_genie.db"
        )
        self.TELEGRAM_BOT_TOKEN: str = os.getenv(
            "TELEGRAM_BOT_TOKEN", os.getenv("BOT_TOKEN", "")
        )
        self.ALPHA_VANTAGE_API_KEY: str = os.getenv("ALPHA_VANTAGE_API_KEY", "")
        self.SESSION_SECRET: str = os.getenv("SESSION_SECRET", "")
        self.ADMIN_TELEGRAM_ID: int = _parse_admin_id()

    def validate(self) -> None:
        errors: list[str] = []
        warnings: list[str] = []

        if not self.TELEGRAM_BOT_TOKEN:
            errors.append("TELEGRAM_BOT_TOKEN is required")

        if not self.SESSION_SECRET:
            errors.append("SESSION_SECRET is required")

        # OPTIONAL services (DO NOT block startup)
        if not self.ALPHA_VANTAGE_API_KEY:
            warnings.append("ALPHA_VANTAGE_API_KEY missing (live prices disabled)")

        if errors:
            raise ValueError("Config errors: " + "; ".join(errors))

        for w in warnings:
            print(f"⚠️ {w}")


config = Config()

# Convenience alias used by bot modules
BOT_TOKEN = config.TELEGRAM_BOT_TOKEN
