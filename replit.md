# Dividend Genie

A Python project for tracking and analysing dividend-paying stocks, featuring a bot interface, services layer, database integration, and data models.

## Project overview

- **`app/bot/`** — Bot handlers (e.g. Telegram commands/callbacks)
- **`app/services/`** — Business logic: dividend calculations, data fetching, notifications
- **`app/database/`** — DB session management, migrations, repository helpers
- **`app/models/`** — SQLAlchemy ORM models and Pydantic schemas
- **`app/config.py`** — Centralised config loaded from `.env`
- **`app/main.py`** — Application entry point
- **`tests/`** — pytest test suite

## Running

```bash
pip install -r requirements.txt
python -m app.main
```

## User preferences

- Project language: Python
- Structure follows the dividend-genie directory layout as specified by the user
