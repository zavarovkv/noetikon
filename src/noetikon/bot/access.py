from functools import wraps

from noetikon.database import async_session
from noetikon.services import user_registry


def require_trusted(func):
    @wraps(func)
    async def wrapper(update, context):
        if not update.effective_chat or not update.effective_user:
            return
        async with async_session() as session:
            trusted = await user_registry.is_trusted(
                session, update.effective_chat.id, update.effective_user.id
            )
        if not trusted:
            return
        return await func(update, context)

    return wrapper
