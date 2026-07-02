import logging
import os
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)


def _parse_admin_id():
    raw = os.getenv("ADMIN_TELEGRAM_ID", "").strip().lstrip("@")
    return int(raw) if raw.isdigit() else 0


class Config:
    def __init__(self):
        self.APP_ENV = os.getenv("APP_ENV", "production")

        self.DATABASE_URL = os.getenv(
            "DATABASE_URL",
            "postgresql+psycopg2://user:pass@localhost:5432/dividend"
        )

        self.TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
        self.ALPHA_VANTAGE_API_KEY = os.getenv("ALPHA_VANTAGE_API_KEY", "")
        self.SESSION_SECRET = os.getenv("SESSION_SECRET", "change-me")

        self.ADMIN_TELEGRAM_ID = _parse_admin_id()

        self.WEBHOOK_URL = os.getenv("WEBHOOK_URL", "")
        self.PORT = int(os.getenv("PORT", "10000"))

    def validate(self):
        errors = []

        if not self.TELEGRAM_BOT_TOKEN:
            errors.append("TELEGRAM_BOT_TOKEN missing")

        if not self.SESSION_SECRET or self.SESSION_SECRET == "change-me":
            errors.append("Invalid SESSION_SECRET")

        if not self.WEBHOOK_URL:
            errors.append("WEBHOOK_URL missing")

        if errors:
            raise ValueError("Config errors: " + "; ".join(errors))


config = Config()

# Convenience alias used by bot modules
BOT_TOKEN = config.TELEGRAM_BOT_TOKEN
