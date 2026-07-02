from typing import Any

import app

from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
)

from app.config import config

from app.bot.commands import (
    start,
    help_command,
    dividend,
    add,
    bonus,
    split,
    stats,
    upcoming,
    upcoming_page_callback,
)
from app.database.session import get_session
from app.services.dividend_calendar_service import get_next_event, get_upcoming_events
from app.services.dividend_engine import calculate_portfolio_dividends
from app.services.portfolio_service import get_user_holdings
from app.services.price_service import get_live_price
from app.services.tracker_service import track



def create_bot():
    app = ApplicationBuilder().token(config.TELEGRAM_BOT_TOKEN).build()

# Commands
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("dividend", dividend))
    app.add_handler(CommandHandler("add", add))
    app.add_handler(CommandHandler("upcoming", upcoming))
    app.add_handler(CommandHandler("bonus", bonus))
    app.add_handler(CommandHandler("split", split))
    app.add_handler(CommandHandler("stats", stats))
   # Callbacks
    app.add_handler(
        CallbackQueryHandler(
            upcoming_page_callback,
            pattern=r"^up\|",
        )
    )
    return app


async def calendar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tg_user = update.effective_user

    holdings = get_user_holdings(tg_user.id)

    if not holdings:
        await update.message.reply_text("No holdings found in your portfolio.")
        return

    message = ["📅 *Your Dividend Calendar*\n"]

    total_income = 0

    for h in holdings:
        event = get_next_event(h.symbol)

        if event:
            income = h.shares * event["dividend_per_share"]
            total_income += income

            message.append(
                f"📌 {h.symbol}\n"
                f"Ex-Date: {event['ex_date']}\n"
                f"Dividend: ₹{event['dividend_per_share']}/share\n"
                f"Your Income: ₹{income:,.2f}\n"
            )
        else:
            message.append(f"📌 {h.symbol}: No upcoming events\n")

    message.append(
        f"\n💰 *Total Expected Dividend Income:* ₹{total_income:,.2f}"
    )

    await update.message.reply_text("\n".join(message), parse_mode="Markdown")

