import logging

from telegram import Update
from telegram.ext import ContextTypes

from noetikon.bot.access import require_trusted
from noetikon.database import async_session
from noetikon.services import group_service
from noetikon.services.llm_service import LLMService

logger = logging.getLogger(__name__)

HUMOR_SYSTEM_PROMPT = """You are a witty bot in a product team Telegram group.
Your job: decide if NOW is a good moment for a short, contextual joke in Russian.

ANTI-TRIGGERS (do NOT joke):
- Production bugs, incidents, outages
- Deadlines, urgent tasks
- Layoffs, conflicts, complaints
- Serious technical discussions about failures

TRIGGERS (more likely to joke):
- Friday chat
- Celebrating wins, shipped features
- Sprint completion
- Casual conversation

If it's appropriate, respond with a short joke in Russian (1-2 sentences) related to the conversation context.
If it's NOT appropriate, respond with exactly: NO_JOKE

Your joke should be natural, as if a colleague said it. Not forced."""


async def maybe_joke(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Called on every message. Checks if it's time for a joke."""
    if not update.effective_chat or not update.message or not update.message.text:
        return

    chat_id = update.effective_chat.id

    # Get group-specific humor frequency
    async with async_session() as session:
        group = await group_service.get_group(session, chat_id)

    humor_frequency = group.humor_frequency if group else context.bot_data["settings"].humor_frequency

    # Increment group message counter
    counter_key = f"humor_counter_{chat_id}"
    count = context.bot_data.get(counter_key, 0) + 1
    context.bot_data[counter_key] = count

    if count % humor_frequency != 0:
        return

    # Collect recent messages from cache for context
    recent = []
    msg_cache = context.bot_data.get("msg_cache", {})
    for user_msgs in msg_cache.values():
        recent.extend(user_msgs)
    recent = recent[-10:]

    if not recent:
        return

    llm: LLMService = context.bot_data["llm"]

    try:
        response, _, _ = await llm.chat(
            messages=[{"role": "user", "content": "Recent chat messages:\n" + "\n".join(recent)}],
            system=HUMOR_SYSTEM_PROMPT,
            max_tokens=200,
        )
        response = response.strip()
        if response and response != "NO_JOKE":
            await update.message.reply_text(response)
    except Exception:
        logger.exception("Humor generation failed")
