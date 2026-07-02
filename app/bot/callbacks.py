from app.services.nse_service import get_upcoming_corporate_actions
from app.bot.utils import format_page

async def upcoming_page_callback(update, context):
    query = update.callback_query
    await query.answer()

    try:
        _, cat, page = query.data.split("|")
        page = int(page)

        items = get_upcoming_corporate_actions(days=30)

        filtered = [x for x in items if x["type"] == cat.upper()]

        text, keyboard = format_page(filtered, cat, page)

        await query.edit_message_text(
            text,
            parse_mode="Markdown",
            reply_markup=keyboard
        )

    except Exception as e:
        await query.answer("Error loading page", show_alert=True)