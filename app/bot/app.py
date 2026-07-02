from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler
from app.config import config

from app.bot.handlers import (
    start, help_command, dividend, add, portfolio,
    bonus, split, upcoming, stats
)

from app.bot.callbacks import upcoming_page_callback


def create_app():
    app = (
        ApplicationBuilder()
        .token(config.TELEGRAM_BOT_TOKEN)
        .build()
    )

    # Commands
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("dividend", dividend))
    app.add_handler(CommandHandler("add", add))
    app.add_handler(CommandHandler("portfolio", portfolio))
    app.add_handler(CommandHandler("bonus", bonus))
    app.add_handler(CommandHandler("split", split))
    app.add_handler(CommandHandler("upcoming", upcoming))
    app.add_handler(CommandHandler("stats", stats))

    # Callbacks
    app.add_handler(
        CallbackQueryHandler(upcoming_page_callback, pattern=r"^up\|")
    )

    return app