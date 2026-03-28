import logging

from telegram import Update
from telegram.ext import ContextTypes

from noetikon.bot.access import require_trusted
from noetikon.database import async_session
from noetikon.services import stats_service
from noetikon.services.llm_service import LLMService

logger = logging.getLogger(__name__)

MAX_TG_MESSAGE_LEN = 4096
MAX_REPLY_CHAIN = 20


def _collect_reply_chain(message, max_depth: int = MAX_REPLY_CHAIN) -> list[dict]:
    """Walk reply chain and build Claude-compatible messages list."""
    chain = []
    current = message
    while current and len(chain) < max_depth:
        if current.text:
            chain.append({"role": "user", "content": current.text})
        current = current.reply_to_message
    chain.reverse()
    return chain


@require_trusted
async def handle_ask(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /ask command."""
    if not update.message or not update.message.text:
        return
    text = update.message.text.removeprefix("/ask").strip()
    if not text:
        await update.message.reply_text("Usage: /ask <your question>")
        return
    await _process_llm_request(update, context, [{"role": "user", "content": text}])


@require_trusted
async def handle_mention(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle @bot mention in regular messages."""
    if not update.message or not update.message.text:
        return
    messages = _collect_reply_chain(update.message)
    if not messages:
        return
    await _process_llm_request(update, context, messages)


async def _process_llm_request(update: Update, context: ContextTypes.DEFAULT_TYPE, messages: list[dict]):
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id
    settings = context.bot_data["settings"]
    llm: LLMService = context.bot_data["llm"]

    # Check rate limit
    async with async_session() as session:
        daily_count = await stats_service.get_daily_request_count(session, chat_id)
    if daily_count >= settings.llm_rate_limit:
        await update.message.reply_text("Limit requests exceeded for today, try again tomorrow.")
        return

    # Send typing indicator
    await update.effective_chat.send_action("typing")

    try:
        response_text, input_tokens, output_tokens = await llm.chat(messages=messages)
    except Exception:
        logger.exception("Claude API error")
        await update.message.reply_text("Error communicating with Claude API. Try again later.")
        return

    # Record usage
    async with async_session() as session:
        await stats_service.record_usage(session, chat_id, user_id, input_tokens, output_tokens)

    # Send response, splitting if necessary
    for i in range(0, len(response_text), MAX_TG_MESSAGE_LEN):
        chunk = response_text[i : i + MAX_TG_MESSAGE_LEN]
        await update.message.reply_text(chunk)
