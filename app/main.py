"""
Entry point — sets up logging, initialises the database, and starts polling.

Manual run:
    source .venv/bin/activate && python -m app.main
"""
from __future__ import annotations

import logging
import logging.handlers
import os
from threading import Thread
import time
from app.services.scheduler import start_scheduler
from app.database.db import init_db
from app.config import config

# ── Logging setup ─────────────────────────────────────────────────────────────
os.makedirs("logs", exist_ok=True)

_fmt = logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")

_console = logging.StreamHandler()
_console.setFormatter(_fmt)

_file = logging.handlers.RotatingFileHandler(
    "logs/app.log", maxBytes=5 * 1024 * 1024, backupCount=3, encoding="utf-8"
)
_file.setFormatter(_fmt)

logging.basicConfig(level=logging.INFO, handlers=[_console, _file])

logger = logging.getLogger(__name__)

# ── Startup ───────────────────────────────────────────────────────────────────
def main() -> None:
    from app.bot.telegram_bot import create_bot

    config.validate()
    init_db()
    logger.info("Database initialised.")
    
    start_scheduler()   # 🔥 NEW APSCHEDULER ENGINE

    bot = create_bot()

    logger.info("🚀 Dividend Genie is running...")
    bot.run_polling()



if __name__ == "__main__":
    main()

