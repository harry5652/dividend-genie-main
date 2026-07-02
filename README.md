# Dividend Genie 🤖💰

A bot/service that helps investors track and analyse dividend-paying stocks.

## Project structure

```
dividend-genie-main/
├── app/
│   ├── bot/
│   │   ├── commands.py         # Telegram command handlers
│   │   └── telegram_bot.py    # Bot bootstrap and message routing
│   ├── data/
│   │   ├── dividend_calendar.py
│   │   └── dividends.py
│   ├── database/
│   │   └── db.py               # SQLAlchemy engine, session factory, migrations
│   ├── models/
│   │   ├── portfolio.py
│   │   └── user.py
│   ├── services/
│   │   ├── alert_scheduler.py
│   │   ├── dividend_calendar_service.py
│   │   ├── dividend_service.py
│   │   ├── logger_service.py
│   │   ├── nse_service.py
│   │   ├── portfolio_service.py
│   │   ├── price_service.py
│   │   ├── scheduler.py
│   │   ├── screener_service.py
│   │   ├── tracker_service.py
│   │   └── user_service.py
│   ├── utils/
│   │   └── formatting.py
│   ├── config.py              # Centralized configuration (reads .env)
│   └── main.py                # Application entry point
├── logs/                      # Runtime logs
├── tests/
│   ├── test_config.py
│   ├── test_placeholder.py
│   ├── test_portfolio_service.py
│   └── test_tracker_service.py
├── requirements.txt           # Python dependencies
├── README.md
└── replit.md
```

## Getting started

1. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure environment**
   Create a local `.env` file and fill in the required values. At minimum, set `SESSION_SECRET` (generate one with
   `python -c "import secrets; print(secrets.token_hex(32))"`).
   In production, `TELEGRAM_BOT_TOKEN` and `ALPHA_VANTAGE_API_KEY` are also required.

3. **Run the application**
   ```bash
   python -m app.main
   ```

4. **Run tests**
   ```bash
   pytest -q
   ```

## Configuration

| Variable | Description | Default |
|---|---|---|
| `APP_ENV` | `development` or `production` | `development` |
| `DATABASE_URL` | SQLAlchemy connection string | `sqlite:///dividend_genie.db` |
| `TELEGRAM_BOT_TOKEN` | Telegram bot token | — |
| `ALPHA_VANTAGE_API_KEY` | Market data API key | — |
| `SESSION_SECRET` | Secret for session signing | — |
