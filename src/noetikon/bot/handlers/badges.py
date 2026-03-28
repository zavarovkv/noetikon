import logging
from collections import deque

from telegram import Update
from telegram.ext import ContextTypes

from noetikon.bot.access import require_trusted
from noetikon.database import async_session
from noetikon.services import user_registry
from noetikon.services.llm_service import LLMService

logger = logging.getLogger(__name__)

MAX_CACHED_MESSAGES = 20

BADGE_SYSTEM_PROMPT = """You generate short Star Wars-themed badges (titles) in Russian for Telegram group members.
Based on the user's recent messages, create a badge that reflects their role or expertise.

STRICT RULES:
- Maximum 16 characters (this is a hard Telegram limit)
- In Russian
- Star Wars themed (use Jedi, Sith, Padawan, Master, etc.)
- Return ONLY the badge text, nothing else

Examples: Лорд метрик, Джедай фичей, Сит бэкенда, Падаван UX"""


def _get_user_messages(context: ContextTypes.DEFAULT_TYPE, user_id: int) -> list[str]:
    """Get cached recent messages for a user."""
    cache = context.bot_data.setdefault("msg_cache", {})
    return list(cache.get(user_id, []))


def _cache_message(context: ContextTypes.DEFAULT_TYPE, user_id: int, text: str):
    """Cache a message for badge generation."""
    cache = context.bot_data.setdefault("msg_cache", {})
    if user_id not in cache:
        cache[user_id] = deque(maxlen=MAX_CACHED_MESSAGES)
    cache[user_id].append(text)


@require_trusted
async def request_badge(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /badge command — manually request a new badge."""
    if not update.effective_chat or not update.effective_user:
        return
    await _assign_badge(update, context, update.effective_chat.id, update.effective_user.id)


async def maybe_assign_badge(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Called on every message. Increments counter, caches message, checks if badge should be assigned."""
    if not update.effective_chat or not update.effective_user or not update.message:
        return

    chat_id = update.effective_chat.id
    user_id = update.effective_user.id
    text = update.message.text
    if not text:
        return

    _cache_message(context, user_id, text)

    async with async_session() as session:
        new_count = await user_registry.increment_message_count(session, chat_id, user_id)
        if new_count == 0:
            return
        user = await user_registry.get_user(session, chat_id, user_id)
        if user and user_registry.should_assign_badge(user):
            await _assign_badge(update, context, chat_id, user_id)


async def _assign_badge(update: Update, context: ContextTypes.DEFAULT_TYPE, chat_id: int, user_id: int):
    """Generate and assign a badge via Claude."""
    llm: LLMService = context.bot_data["llm"]
    messages_cache = _get_user_messages(context, user_id)

    if not messages_cache:
        user_context = "No recent messages available."
    else:
        user_context = "\n".join(messages_cache[-10:])

    try:
        badge, _, _ = await llm.chat(
            messages=[{"role": "user", "content": f"Messages from this user:\n{user_context}"}],
            system=BADGE_SYSTEM_PROMPT,
            max_tokens=50,
        )
        badge = badge.strip()

        # Enforce 16 char limit — retry once if too long
        if len(badge) > 16:
            badge, _, _ = await llm.chat(
                messages=[
                    {"role": "user", "content": f"Messages from this user:\n{user_context}"},
                    {"role": "assistant", "content": badge},
                    {"role": "user", "content": f"Too long ({len(badge)} chars). Must be 16 chars max. Try again, shorter."},
                ],
                system=BADGE_SYSTEM_PROMPT,
                max_tokens=50,
            )
            badge = badge.strip()[:16]

    except Exception:
        logger.exception("Failed to generate badge")
        return

    try:
        await context.bot.set_chat_administrator_custom_title(
            chat_id=chat_id, user_id=user_id, custom_title=badge
        )
    except Exception:
        logger.exception("Failed to set custom title for user %s", user_id)
        return

    async with async_session() as session:
        user = await user_registry.get_user(session, chat_id, user_id)
        if user:
            await user_registry.update_badge(session, user.id, badge)

    logger.info("Assigned badge '%s' to user %s in group %s", badge, user_id, chat_id)
