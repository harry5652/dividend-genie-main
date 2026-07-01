try:
    from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler
except ImportError:  # pragma: no cover - optional dependency
    ApplicationBuilder = None
    CommandHandler = None
    CallbackQueryHandler = None

from app.config import config
from app.bot.commands import (
    start, help_command, dividend, upcoming, upcoming_page_callback,
    bonus, split, stats, add,
)
from telegram import Update
from telegram.ext import ContextTypes

from app.database.db import SessionLocal
from app.models.user import User
from app.models.portfolio import Portfolio
from telegram.ext import CommandHandler
from app.services.tracker_service import track
from app.services.dividend_service import calculate_dividend_income
from app.services.price_service import get_live_price
from app.services.dividend_calendar_service import get_upcoming_events, get_next_event
from app.services.portfolio_service import get_user_holdings


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

async def portfolio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print("👉 /portfolio triggered") 
    tg_user = update.effective_user

    session = SessionLocal()

    try:
        # track usage
        track(tg_user, "/portfolio")

        # find user
        user = session.query(User).filter_by(telegram_id=tg_user.id).first()

        if not user:
            await update.message.reply_text("No portfolio found. Add stocks using /add command.")
            return

        holdings = session.query(Portfolio).filter_by(user_id=user.id).all()

        if not holdings:
            await update.message.reply_text("📭 Your portfolio is empty. Add stocks using /add.")
            return

        message_lines = ["📊 *Your Portfolio*\n"]
        total_invested = 0
        total_current = 0
        total_dividend_yearly = 0


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


            div = calculate_dividend_income(h.symbol.replace(".NS", ""), h.shares)

            if div:
                total_dividend_yearly += div["yearly"]

                message_lines.append(
                    f"💰 Dividend Income:\n"
                    f"Yearly: ₹{div['yearly']:,.2f}\n"
                    f"Monthly: ₹{div['monthly']:,.2f}\n"
                    f"Yield: {div['yield_percent']}%\n"
    )
            else:
                message_lines.append("💰 Dividend: Not available\n")

        total_pnl = total_current - total_invested
        total_pct = (total_pnl / total_invested) * 100 if total_invested else 0

        message_lines.append(
            f"\n💰 *Total Invested:* ₹{total_invested:,.2f}\n"
            f"📈 *Current Value:* ₹{total_current:,.2f}\n"
            f"📊 *Total P&L:* ₹{total_pnl:,.2f} ({total_pct:.2f}%)'"
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

