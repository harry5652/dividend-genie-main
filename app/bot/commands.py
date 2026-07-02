from __future__ import annotations

import logging
from typing import Any

from app.models.portfolio import Portfolio
from app.models.user import User
from app.services.dividend_engine import calculate_portfolio_dividends
from app.services.price_service import get_live_price
from app.services.tracker_service import track
from app.database.session import get_session

from app.services.dividend_service import get_dividend_info, format_dividend_message
from app.services.portfolio_service import add_holding
from app.services.tracker_service import track, get_stats
from app.services.nse_service import (
    get_upcoming_corporate_actions,
    get_symbol_bonus_history,
    get_symbol_split_history,
)

try:
    from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
    from telegram.ext import ContextTypes
except ImportError:  # pragma: no cover - optional dependency
    Update = Any
    InlineKeyboardButton = lambda *args, **kwargs: None
    InlineKeyboardMarkup = lambda *args, **kwargs: None

    class ContextTypes:  # type: ignore[no-redef]
        DEFAULT_TYPE = Any


logger = logging.getLogger(__name__)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tg_user = update.effective_user
    track(tg_user, "start")
    logger.info("/start from %s", tg_user.first_name)
    await update.message.reply_text(
        f"👋 Welcome to Dividend Genie, {tg_user.first_name}!\n\n"
        "Your assistant for NSE, BSE & global dividend stocks.\n\n"
        "Commands:\n"
        "  /dividend ITC — dividend info\n"
        "  /dividend ITC 100 — payout for 100 shares\n"
        "  /upcoming — dividends due in 30 days\n"
        "  /help — full guide"
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    track(update.effective_user, "help")
    logger.info("/help requested")
    await update.message.reply_text(
        "📖 *Available Commands*\n\n"
        "/dividend `<symbol>` — Full dividend info\n"
        "/dividend `<symbol>` `<shares>` — With estimated payout\n"
        "/upcoming — Upcoming dividends in next 30 days\n\n"
        "*Exchange suffixes:*\n"
        "  `.NS` → NSE    `.BO` → BSE\n"
        "  No suffix → auto\\-detect (tries NSE then BSE)\n\n"
        "*Examples:*\n"
        "  `/dividend ITC`\n"
        "  `/dividend ITC 500`\n"
        "  `/dividend RELIANCE.NS 100`\n"
        "  `/dividend HDFCBANK.BO`\n"
        "  `/dividend AAPL`",
        parse_mode="Markdown",
    )


async def add(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) != 3:
        await update.message.reply_text(
            "Usage:\n"
            "  /add ITC 25 420\n\n"
            "That means: symbol ITC, 25 shares, buy price 420."
        )
        return

    symbol = context.args[0].upper().strip()

    try:
        shares = int(context.args[1].replace(",", ""))
        price = float(context.args[2].replace(",", ""))
    except ValueError:
        await update.message.reply_text(
            "Shares must be a whole number and price must be numeric. Example: /add ITC 25 420"
        )
        return

    track(update.effective_user, "add", " ".join(context.args))

    try:
        result = add_holding(update.effective_user, symbol, shares, price)
    except ValueError as exc:
        await update.message.reply_text(str(exc))
        return
    except Exception as exc:
        print("❌ ADD ERROR:", exc)
        await update.message.reply_text(f"Error: {exc}")
        return

    action = "Added" if result.is_new else "Updated"
    await update.message.reply_text(
        f"{action} {result.symbol}\n"
        f"Shares: {result.shares:,}\n"
        f"Average price: {result.avg_price:,.2f}\n"
        f"Invested value: {result.total_invested:,.2f}"
    )


async def dividend(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text(
            "Usage:\n"
            "  /dividend ITC\n"
            "  /dividend ITC 100   ← add shares for payout estimate"
        )
        return

    symbol = context.args[0].upper()
    shares = None

    if len(context.args) >= 2:
        try:
            shares = int(context.args[1].replace(",", ""))
            if shares <= 0:
                raise ValueError
        except ValueError:
            await update.message.reply_text("⚠️ Shares must be a positive number. E.g. /dividend ITC 100")
            return

    track(update.effective_user, "dividend", " ".join(context.args))
    logger.info("Dividend lookup: symbol=%s shares=%s", symbol, shares)
    wait_msg = await update.message.reply_text(
        f"🔍 Looking up *{symbol}*...", parse_mode="Markdown"
    )

    try:
        data = get_dividend_info(symbol, shares)
        msg = format_dividend_message(data)
        await wait_msg.edit_text(msg, parse_mode="Markdown", disable_web_page_preview=True)

    except ValueError as e:
        logger.warning("Lookup failed %s: %s", symbol, e)
        await wait_msg.edit_text(f"❌ {e}")

    except Exception as e:
        logger.error("Error for %s: %s", symbol, e, exc_info=True)
        await wait_msg.edit_text("⚠️ Something went wrong. Check Console logs for details.")


def _format_action_block(i: int, item: dict) -> str:
    """Format one corporate action entry for the /upcoming list."""
    ex_dt  = item["ex_date"].strftime("%d-%b-%Y")
    rec_dt = item["record_date"].strftime("%d-%b-%Y") if item["record_date"] else "N/A"
    header = f"{i}. *{item['company']}* ({item['symbol']})"

    if item["type"] == "DIVIDEND":
        amount = f"₹{item['amount']:.2f}/share" if item.get("amount") else item.get("subject", "N/A")
        detail = f"   💰 Dividend: {amount}"

    elif item["type"] == "BONUS":
        ratio  = item.get("ratio") or "N/A"
        detail = f"   🎁 Bonus Issue: {ratio}"

    else:  # SPLIT
        face   = item.get("face_change")
        ratio  = item.get("ratio")
        if face:
            detail = f"   ✂️ Stock Split: {face}"
        elif ratio:
            detail = f"   ✂️ Stock Split: {ratio}"
        else:
            detail = f"   ✂️ Stock Split"

    return (
        f"{header}\n"
        f"{detail}\n"
        f"   📅 Ex-Date: {ex_dt}\n"
        f"   📋 Record Date: {rec_dt}"
    )


async def bonus(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text(
            "Usage: /bonus <symbol>\nExample: /bonus INFY"
        )
        return

    symbol = context.args[0].upper()
    track(update.effective_user, "bonus", symbol)
    logger.info("Bonus history requested: %s", symbol)
    wait_msg = await update.message.reply_text(f"🎁 Fetching bonus history for *{symbol}*...", parse_mode="Markdown")

    try:
        items = get_symbol_bonus_history(symbol)

        if not items:
            await wait_msg.edit_text(f"ℹ️ No bonus issue history found for *{symbol}*.", parse_mode="Markdown")
            return

        lines = [f"🎁 *Bonus Issue History — {symbol}* ({len(items)} records)\n"]
        for i, item in enumerate(items[:10], 1):
            ex_dt  = item["ex_date"].strftime("%d-%b-%Y")  if item.get("ex_date")     else "N/A"
            rec_dt = item["record_date"].strftime("%d-%b-%Y") if item.get("record_date") else "N/A"
            ratio  = item.get("ratio") or "N/A"
            lines.append(
                f"{i}. 🎁 Bonus: *{ratio}*\n"
                f"   📅 Ex-Date: {ex_dt}\n"
                f"   📋 Record Date: {rec_dt}"
            )

        await wait_msg.edit_text("\n\n".join(lines), parse_mode="Markdown")

    except Exception as e:
        logger.error("Error in /bonus for %s: %s", symbol, e, exc_info=True)
        await wait_msg.edit_text("⚠️ Could not fetch bonus history. Please try again later.")


async def split(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text(
            "Usage: /split <symbol>\nExample: /split TCS"
        )
        return

    symbol = context.args[0].upper()
    track(update.effective_user, "split", symbol)
    logger.info("Split history requested: %s", symbol)
    wait_msg = await update.message.reply_text(f"✂️ Fetching split history for *{symbol}*...", parse_mode="Markdown")

    try:
        items = get_symbol_split_history(symbol)

        if not items:
            await wait_msg.edit_text(f"ℹ️ No stock split history found for *{symbol}*.", parse_mode="Markdown")
            return

        lines = [f"✂️ *Stock Split History — {symbol}* ({len(items)} records)\n"]
        for i, item in enumerate(items[:10], 1):
            ex_dt  = item["ex_date"].strftime("%d-%b-%Y")    if item.get("ex_date")     else "N/A"
            rec_dt = item["record_date"].strftime("%d-%b-%Y") if item.get("record_date") else "N/A"
            face   = item.get("face_change")
            ratio  = item.get("ratio")
            detail = face or (f"Ratio {ratio}" if ratio else item.get("subject", "N/A"))
            lines.append(
                f"{i}. ✂️ Split: *{detail}*\n"
                f"   📅 Ex-Date: {ex_dt}\n"
                f"   📋 Record Date: {rec_dt}"
            )

        await wait_msg.edit_text("\n\n".join(lines), parse_mode="Markdown")

    except Exception as e:
        logger.error("Error in /split for %s: %s", symbol, e, exc_info=True)
        await wait_msg.edit_text("⚠️ Could not fetch split history. Please try again later.")


PAGE_SIZE = 5

# ── Pagination helpers ────────────────────────────────────────────────────────

_TYPE_META = {
    "div":   ("DIVIDEND", "💰 Dividends"),
    "bonus": ("BONUS",    "🎁 Bonus Issues"),
    "split": ("SPLIT",    "✂️ Stock Splits"),
}


def _category_keyboard(cat: str, page: int, total: int) -> InlineKeyboardMarkup:
    """Build Prev / Next inline buttons for a paginated category view."""
    buttons: list[InlineKeyboardButton] = []
    if page > 0:
        buttons.append(InlineKeyboardButton("⬅️ Prev", callback_data=f"up|{cat}|{page - 1}"))
    if (page + 1) * PAGE_SIZE < total:
        buttons.append(InlineKeyboardButton("Next ➡️", callback_data=f"up|{cat}|{page + 1}"))
    return InlineKeyboardMarkup([buttons]) if buttons else InlineKeyboardMarkup([])


def _build_category_page(items: list[dict], cat: str, page: int) -> tuple[str, InlineKeyboardMarkup]:
    """Return (text, keyboard) for a single paginated category page."""
    _, label = _TYPE_META[cat]
    total    = len(items)
    start    = page * PAGE_SIZE
    chunk    = items[start: start + PAGE_SIZE]
    last     = min(start + PAGE_SIZE, total)

    lines = [f"{label} — Page {page + 1}  ({start + 1}–{last} of {total})\n"]
    for i, item in enumerate(chunk, start + 1):
        lines.append(_format_action_block(i, item))

    return "\n\n".join(lines), _category_keyboard(cat, page, total)


def _main_upcoming_message(
    dividends: list, bonuses: list, splits: list
) -> tuple[str, InlineKeyboardMarkup]:
    """Build the initial /upcoming message with first 5 per category + More buttons."""
    lines   = ["📅 *Upcoming Corporate Actions — Next 30 Days*\n"]
    buttons = []

    for cat, items, label in [
        ("div",   dividends, "💰 Dividends"),
        ("bonus", bonuses,   "🎁 Bonus Issues"),
        ("split", splits,    "✂️ Stock Splits"),
    ]:
        if not items:
            continue
        lines.append(f"{label} ({len(items)})")
        for i, item in enumerate(items[:PAGE_SIZE], 1):
            lines.append(_format_action_block(i, item))
        if len(items) > PAGE_SIZE:
            remaining = len(items) - PAGE_SIZE
            buttons.append(
                InlineKeyboardButton(
                    f"➡️ More {label} ({remaining} more)",
                    callback_data=f"up|{cat}|1",
                )
            )
        lines.append("")  # spacer

    keyboard = InlineKeyboardMarkup([[b] for b in buttons])
    return "\n\n".join(lines).strip(), keyboard


# ── /upcoming command ─────────────────────────────────────────────────────────

async def upcoming(update: Update, context: ContextTypes.DEFAULT_TYPE):
    track(update.effective_user, "upcoming")
    logger.info("/upcoming requested")
    wait_msg = await update.message.reply_text(
        "📅 Fetching upcoming corporate actions from NSE..."
    )

    try:
        items = get_upcoming_corporate_actions(days=30)

        if not items:
            await wait_msg.edit_text(
                "ℹ️ No upcoming dividends, bonus issues, or stock splits found in the next 30 days."
            )
            return

        dividends = [a for a in items if a["type"] == "DIVIDEND"]
        bonuses   = [a for a in items if a["type"] == "BONUS"]
        splits    = [a for a in items if a["type"] == "SPLIT"]

        text, keyboard = _main_upcoming_message(dividends, bonuses, splits)
        await wait_msg.edit_text(text, parse_mode="Markdown", reply_markup=keyboard)

    except Exception as e:
        logger.error("Error in /upcoming: %s", e, exc_info=True)
        await wait_msg.edit_text("⚠️ Could not fetch upcoming actions. Please try again later.")


# ── Pagination callback ───────────────────────────────────────────────────────

async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    from app.config import config
    if update.effective_user.id != config.ADMIN_TELEGRAM_ID:
        await update.message.reply_text("⛔ This command is restricted to the admin.")
        return
    track(update.effective_user, "stats")
    logger.info("/stats requested by admin")
    wait_msg = await update.message.reply_text("📊 Fetching usage stats...")

    try:
        s = get_stats()
        if not s:
            await wait_msg.edit_text("⚠️ Could not load stats right now.")
            return

        top_cmds = "\n".join(
            f"   {i+1}. /{r['command']} — {r['count']} times"
            for i, r in enumerate(s.get("top_commands", []))
        ) or "   No data yet"

        top_users = "\n".join(
            f"   {i+1}. {r['name']}" + (f" (@{r['username']})" if r['username'] else "") +
            f" — {r['commands']} commands"
            for i, r in enumerate(s.get("top_users", []))
        ) or "   No data yet"

        msg = (
            "📊 *Dividend Genie — Usage Stats*\n\n"
            f"👥 Total Users:       {s['total_users']:,}\n"
            f"🟢 Active Today:      {s['active_today']:,}\n"
            f"📅 Active This Week:  {s['active_week']:,}\n"
            f"🗓 Active This Month: {s['active_month']:,}\n"
            f"⚡ Total Commands:   {s['total_commands']:,}\n\n"
            f"🏆 *Top Commands:*\n{top_cmds}\n\n"
            f"🥇 *Most Active Users:*\n{top_users}"
        )
        await wait_msg.edit_text(msg, parse_mode="Markdown")

    except Exception as e:
        logger.error("Error in /stats: %s", e, exc_info=True)
        await wait_msg.edit_text("⚠️ Could not fetch stats. Please try again later.")


async def upcoming_page_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle ⬅️ Prev / Next ➡️ button presses for /upcoming pagination."""
    query = update.callback_query
    await query.answer()

    try:
        _, cat, page_str = query.data.split("|")
        page = int(page_str)
        action_type, _ = _TYPE_META[cat]
    except (ValueError, KeyError):
        await query.answer("Invalid pagination data.", show_alert=True)
        return

    try:
        all_items = get_upcoming_corporate_actions(days=30)
        items = [a for a in all_items if a["type"] == "DIVIDEND"] if cat == "div" \
            else [a for a in all_items if a["type"] == "BONUS"]   if cat == "bonus" \
            else [a for a in all_items if a["type"] == "SPLIT"]

        if not items:
            await query.edit_message_text("ℹ️ No items found.")
            return

        # Clamp page to valid range
        page = max(0, min(page, (len(items) - 1) // PAGE_SIZE))
        text, keyboard = _build_category_page(items, cat, page)
        await query.edit_message_text(text, parse_mode="Markdown", reply_markup=keyboard)

    except Exception as e:
        logger.error("Pagination callback error: %s", e, exc_info=True)
        await query.answer("⚠️ Could not load page. Please try again.", show_alert=True)


async def portfolio(update, context):
    tg_user = update.effective_user
    track(tg_user, "portfolio")

    with get_session() as session:

        user = session.query(User).filter_by(telegram_id=tg_user.id).first()

        if not user:
            await update.message.reply_text("No portfolio found.")
            return

        holdings = session.query(Portfolio).filter_by(user_id=user.id).all()

        if not holdings:
            await update.message.reply_text("Empty portfolio.")
            return

        holdings_data = [
            {"symbol": h.symbol, "shares": h.shares, "avg_price": h.avg_price}
            for h in holdings
        ]

    # 👇 outside DB session (important for production stability)
    dividend_result = calculate_portfolio_dividends(holdings_data)
    total_dividend_yearly = dividend_result.get("total_yearly", 0)

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

