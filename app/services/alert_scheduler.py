from datetime import datetime, timedelta
from app.services.portfolio_service import get_all_users_with_holdings
from app.services.dividend_calendar_service import get_next_event
from telegram import Bot
from app.config import Config

BOT_TOKEN = Config.TELEGRAM_BOT_TOKEN

def check_and_send_alerts():
    bot = Bot(token=BOT_TOKEN)

    users = get_all_users_with_holdings()

    today = datetime.utcnow().date()
    tomorrow = today + timedelta(days=1)

    for user, holdings in users:

        messages = []

        for h in holdings:
            event = get_next_event(h.symbol)

            if not event:
                continue

            ex_date = datetime.strptime(event["ex_date"], "%Y-%m-%d").date()

            # 🔥 ALERT RULES
            if ex_date == tomorrow:
                messages.append(
                    f"⚠️ *DIVIDEND ALERT*\n\n"
                    f"📌 {h.symbol}\n"
                    f"Ex-Date: {event['ex_date']}\n"
                    f"Dividend: ₹{event['dividend_per_share']}/share\n\n"
                    f"⏳ Last chance to buy today!"
                )

            elif ex_date == today:
                messages.append(
                    f"🚨 *EX-DATE TODAY*\n\n"
                    f"📌 {h.symbol}\n"
                    f"Don’t buy after market close!"
                )

        if messages:
            for msg in messages:
                bot.send_message(
                    chat_id=user.telegram_id,
                    text=msg,
                    parse_mode="Markdown"
                )