# Dividend Genie 🤖💰

A bot/service that helps investors track and analyse dividend-paying stocks.

## Project structure

```
dividend-genie/
├── app/
│   ├── bot/          # Bot handlers (e.g. Telegram commands)
│   ├── services/     # Business logic (dividend calculations, data fetching)
│   ├── database/     # DB session, migrations, repository helpers
│   ├── models/       # SQLAlchemy / Pydantic models
│   ├── config.py     # Centralised configuration (reads from .env)
│   └── main.py       # Application entry point
├── tests/            # pytest test suite
├── requirements.txt  # Python dependencies
├── .env              # Local environment variables (not committed)
└── README.md
```

## Getting started

1. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure environment**
   Copy the example file and fill in the required values:
   ```bash
   cp .env.example .env
   ```
   At minimum you must set `SESSION_SECRET` (generate one with
   `python -c "import secrets; print(secrets.token_hex(32))"`).
   In production, `TELEGRAM_BOT_TOKEN` and `ALPHA_VANTAGE_API_KEY` are also required.

3. **Run the application**
   ```bash
   python -m app.main
   ```

4. **Run tests**
   ```bash
   pytest
   ```

## Configuration

| Variable | Description | Default |
|---|---|---|
| `APP_ENV` | `development` or `production` | `development` |
| `DATABASE_URL` | SQLAlchemy connection string | `sqlite:///dividend_genie.db` |
| `TELEGRAM_BOT_TOKEN` | Telegram bot token | — |
| `ALPHA_VANTAGE_API_KEY` | Market data API key | — |
| `SESSION_SECRET` | Secret for session signing | — |
