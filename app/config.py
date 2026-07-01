"""
Application configuration.
Loads settings from environment variables / .env file.
"""
from __future__ import annotations

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
        if not self.SESSION_SECRET:
            errors.append("SESSION_SECRET must be set in the environment.")
        elif self.SESSION_SECRET in {"change-me", "changeme", "secret", "password"}:
            errors.append(
                "SESSION_SECRET is set to a known insecure default value. "
                "Please generate a strong random secret."
            )
        if self.APP_ENV == "production":
            if not self.TELEGRAM_BOT_TOKEN:
                errors.append("TELEGRAM_BOT_TOKEN must be set in production.")
            if not self.ALPHA_VANTAGE_API_KEY:
                errors.append("ALPHA_VANTAGE_API_KEY must be set in production.")
        if errors:
            detail = "; ".join(errors)
            raise ValueError(
                f"Invalid configuration ({len(errors)} error(s)): {detail}"
            )


config = Config()

# Convenience alias used by bot modules
BOT_TOKEN = config.TELEGRAM_BOT_TOKEN
