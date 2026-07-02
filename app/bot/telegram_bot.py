from typing import Any

try:
    from telegram import Update
    from telegram.ext import (
        ApplicationBuilder,
        CallbackQueryHandler,
        CommandHandler,
        ContextTypes,
    )
except ImportError:  # pragma: no cover - optional dependency
    Update = Any
    ApplicationBuilder = None
    CommandHandler = None
    CallbackQueryHandler = None

    class ContextTypes:  # type: ignore[no-redef]
        DEFAULT_TYPE = Any

from app.config import config
from app.bot.commands import (
    add,
    bonus,
    dividend,
    help_command,
    split,
    start,
    stats,
    upcoming,
    upcoming_page_callback,
)
from app.database.db import SessionLocal
from app.models.portfolio import Portfolio
from app.models.user import User
from app.services.dividend_calendar_service import get_next_event, get_upcoming_events
from app.services.dividend_engine import calculate_portfolio_dividends
from app.services.portfolio_service import get_user_holdings
from app.services.price_service import get_live_price
from app.services.tracker_service import track


def create_bot():
    if ApplicationBuilder is None:
        raise RuntimeError("python-telegram-bot is required to create the bot")

    app = ApplicationBuilder().token(config.TELEGRAM_BOT_TOKEN).build()

    app.add_handler(CommandHandler("start",    start))
    app.add_handler(CommandHandler("help",     help_command))
    app.add_handler(CommandHandler("dividend", dividend))
    app.add_handler(CommandHandler("upcoming", upcoming))
    app.add_handler(CommandHandler("bonus",    bonus))
    app.add_handler(CommandHandler("split",    split))
    app.add_handler(CommandHandler("stats",    stats))
    app.add_handler(CommandHandler("add",      add))
    app.add_handler(CommandHandler("portfolio", portfolio))
    app.add_handler(CommandHandler("calendar", calendar))

    # Pagination buttons for /upcoming
    app.add_handler(CallbackQueryHandler(upcoming_page_callback, pattern=r"^up\|"))

    return app

async def upcoming_page_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    page = int(query.data.split("|")[1])
    events, total_pages = get_upcoming_events(page=page)

    message_lines = [f"📅 *Upcoming Dividend Events (Page {page}/{total_pages})*\n"]

    for event in events:
        message_lines.append(
            f"📌 {event['symbol']}\n"
            f"Ex-Date: {event['ex_date']}\n"
            f"Dividend: ₹{event['dividend_per_share']}/share\n"
        )

    # Add pagination buttons
    buttons = []
    if page > 1:
        buttons.append(f"⬅️ Previous (Page {page - 1})")
    if page < total_pages:
        buttons.append(f"Next (Page {page + 1}) ➡️")

    if buttons:
        message_lines.append("\n".join(buttons))

    await query.edit_message_text("\n".join(message_lines), parse_mode="Markdown")


async def portfolio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tg_user = update.effective_user

    session = SessionLocal()

    try:
        track(tg_user, "/portfolio")

        user = session.query(User).filter(User.telegram_id == tg_user.id).first()

        if not user:
            await update.message.reply_text("No portfolio found. Add stocks using /add command.")
            return

        holdings = session.query(Portfolio).filter(Portfolio.user_id == user.id).all()

        if not holdings:
            await update.message.reply_text("📭 Your portfolio is empty. Add stocks using /add.")
            return

        holdings_data = [
            {"symbol": h.symbol, "shares": h.shares, "avg_price": h.avg_price}
            for h in holdings
        ]
        dividend_result = calculate_portfolio_dividends(holdings_data)
        total_dividend_yearly = dividend_result["total_yearly"]

        message_lines = ["📊 *Your Portfolio*\n"]
        total_invested = 0
        total_current = 0

        for h in holdings:
            invested = h.shares * h.avg_price
            total_invested += invested

            live_price = get_live_price(h.symbol)

            if live_price:
                current_value = h.shares * live_price
                pnl = current_value - invested
                pnl_pct = (pnl / invested) * 100 if invested else 0

                total_current += current_value

                message_lines.append(
                    f"📌 {h.symbol}\n"
                    f"Shares: {h.shares}\n"
                    f"Avg: ₹{h.avg_price:,.2f}\n"
                    f"Live: ₹{live_price:,.2f}\n"
                    f"Invested: ₹{invested:,.2f}\n"
                    f"Value: ₹{current_value:,.2f}\n"
                    f"P&L: ₹{pnl:,.2f} ({pnl_pct:.2f}%)\n"
                )
            else:
                message_lines.append(
                    f"📌 {h.symbol}\n"
                    f"Shares: {h.shares}\n"
                    f"Avg: ₹{h.avg_price:,.2f}\n"
                    f"Live: ❌ Not available\n"
                )

        total_pnl = total_current - total_invested
        total_pct = (total_pnl / total_invested) * 100 if total_invested else 0

        message_lines.append(
            f"\n💰 *Total Invested:* ₹{total_invested:,.2f}\n"
            f"📈 *Current Value:* ₹{total_current:,.2f}\n"
            f"📊 *Total P&L:* ₹{total_pnl:,.2f} ({total_pct:.2f}%)"
        )

        monthly_income = total_dividend_yearly / 12

        message_lines.append(
            f"\n💰 *Dividend Summary*\n"
            f"📅 Yearly Income: ₹{total_dividend_yearly:,.2f}\n"
            f"📆 Monthly Income: ₹{monthly_income:,.2f}\n"
        )

        await update.message.reply_text("\n".join(message_lines), parse_mode="Markdown")

    finally:
        session.close()


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

