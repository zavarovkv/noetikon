from telegram.ext import Application, CommandHandler, MessageHandler, filters

from noetikon.bot.handlers import badges, humor, llm_proxy, meetings


def register_handlers(app: Application):
    # Commands
    app.add_handler(CommandHandler("badge", badges.request_badge))
    app.add_handler(CommandHandler("ask", llm_proxy.handle_ask))

    # Mention-based handlers (meetings checked first, then LLM)
    app.add_handler(MessageHandler(
        filters.TEXT & filters.Entity("mention") & filters.Regex(r"(?i)(встреч|meet|sync|созвон)"),
        meetings.handle_meeting_request,
    ))
    app.add_handler(MessageHandler(
        filters.TEXT & filters.Entity("mention"),
        llm_proxy.handle_mention,
    ))

    # Catch-all for message counting, badge checks, humor
    app.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND,
        _on_message,
    ))


async def _on_message(update, context):
    """Process every text message: count, check badges, check humor."""
    if not update.effective_chat or not update.effective_user or not update.message:
        return

    from noetikon.bot.handlers.badges import maybe_assign_badge
    from noetikon.bot.handlers.humor import maybe_joke

    await maybe_assign_badge(update, context)
    await maybe_joke(update, context)
