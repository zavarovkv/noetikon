import datetime
import json
import logging

from telegram import Update
from telegram.ext import ContextTypes

from noetikon.bot.access import require_trusted
from noetikon.config import get_settings
from noetikon.database import async_session
from noetikon.services import user_registry
from noetikon.services.calendar_service import CalendarService
from noetikon.services.llm_service import LLMService

logger = logging.getLogger(__name__)

MEETING_PARSE_PROMPT = """Extract meeting details from the user's message. Return a JSON object with:
- "title": meeting title (string)
- "date": date in YYYY-MM-DD format (string)
- "time": time in HH:MM format (string)
- "duration_minutes": duration in minutes (integer, default 60)
- "participants": list of @usernames mentioned (list of strings), empty if "all"

Today is {today}. If the user says "tomorrow", calculate the actual date.
Return ONLY valid JSON, nothing else."""


@require_trusted
async def handle_meeting_request(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle meeting scheduling requests."""
    if not update.message or not update.message.text or not update.effective_chat:
        return

    llm: LLMService = context.bot_data["llm"]
    text = update.message.text
    today = datetime.date.today().isoformat()

    try:
        response, _, _ = await llm.chat(
            messages=[{"role": "user", "content": text}],
            system=MEETING_PARSE_PROMPT.format(today=today),
            max_tokens=300,
        )
        meeting = json.loads(response.strip())
    except (json.JSONDecodeError, Exception):
        logger.exception("Failed to parse meeting request")
        await update.message.reply_text("Could not understand the meeting request. Try: @bot meeting tomorrow 15:00 — topic")
        return

    # Build datetime
    try:
        start = datetime.datetime.fromisoformat(f"{meeting['date']}T{meeting['time']}:00")
        duration = meeting.get("duration_minutes", 60)
        end = start + datetime.timedelta(minutes=duration)
    except (KeyError, ValueError):
        await update.message.reply_text("Could not parse date/time. Try: @bot meeting 2026-04-01 15:00 — topic")
        return

    # Resolve participants
    chat_id = update.effective_chat.id
    participants = meeting.get("participants", [])

    async with async_session() as session:
        if not participants:
            users = await user_registry.get_users_by_group(session, chat_id)
        else:
            users = []
            for username in participants:
                username = username.lstrip("@")
                all_users = await user_registry.get_users_by_group(session, chat_id)
                for u in all_users:
                    if u.tg_username and u.tg_username.lower() == username.lower():
                        users.append(u)

    emails = []
    missing = []
    for u in users:
        if u.email:
            emails.append(u.email)
        elif u.tg_username:
            missing.append(f"@{u.tg_username}")

    # Create calendar event
    settings = get_settings()
    calendar = CalendarService(url=settings.caldav_url, username=settings.caldav_username, password=settings.caldav_password)

    try:
        await calendar.create_event(
            title=meeting.get("title", "Meeting"),
            start=start,
            end=end,
            attendee_emails=emails,
        )
    except Exception:
        logger.exception("Failed to create calendar event")
        await update.message.reply_text("Failed to create calendar event. Check CalDAV settings.")
        return

    # Build confirmation message
    title = meeting.get("title", "Meeting")
    msg = f"Meeting created: **{title}**\n"
    msg += f"When: {start.strftime('%d.%m.%Y %H:%M')} — {end.strftime('%H:%M')}\n"
    msg += f"Invited: {len(emails)} participants"
    if missing:
        msg += f"\nNo email for: {', '.join(missing)}"

    await update.message.reply_text(msg, parse_mode="Markdown")
