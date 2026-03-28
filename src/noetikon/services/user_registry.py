import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from noetikon.models.user import TrustedUser


async def get_user(session: AsyncSession, group_id: int, tg_user_id: int) -> TrustedUser | None:
    result = await session.execute(
        select(TrustedUser).where(TrustedUser.group_id == group_id, TrustedUser.tg_user_id == tg_user_id)
    )
    return result.scalar_one_or_none()


async def get_user_by_id(session: AsyncSession, user_id: int) -> TrustedUser | None:
    return await session.get(TrustedUser, user_id)


async def get_users_by_group(session: AsyncSession, group_id: int) -> list[TrustedUser]:
    result = await session.execute(select(TrustedUser).where(TrustedUser.group_id == group_id))
    return list(result.scalars().all())


async def get_all_users(session: AsyncSession) -> list[TrustedUser]:
    result = await session.execute(select(TrustedUser).order_by(TrustedUser.group_id, TrustedUser.tg_username))
    return list(result.scalars().all())


async def is_trusted(session: AsyncSession, group_id: int, tg_user_id: int) -> bool:
    result = await session.execute(
        select(TrustedUser.is_trusted).where(
            TrustedUser.group_id == group_id,
            TrustedUser.tg_user_id == tg_user_id,
            TrustedUser.is_trusted.is_(True),
        )
    )
    return result.scalar_one_or_none() is not None


async def create_user(
    session: AsyncSession,
    group_id: int,
    tg_user_id: int,
    tg_username: str | None = None,
    email: str | None = None,
    is_trusted: bool = True,
) -> TrustedUser:
    user = TrustedUser(
        group_id=group_id,
        tg_user_id=tg_user_id,
        tg_username=tg_username,
        email=email,
        is_trusted=is_trusted,
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user


async def update_user(session: AsyncSession, user_id: int, **kwargs) -> TrustedUser | None:
    user = await session.get(TrustedUser, user_id)
    if user is None:
        return None
    for key, value in kwargs.items():
        setattr(user, key, value)
    await session.commit()
    await session.refresh(user)
    return user


async def delete_user(session: AsyncSession, user_id: int) -> None:
    user = await session.get(TrustedUser, user_id)
    if user:
        await session.delete(user)
        await session.commit()


async def increment_message_count(session: AsyncSession, group_id: int, tg_user_id: int) -> int:
    user = await get_user(session, group_id, tg_user_id)
    if user is None:
        return 0
    user.message_count += 1
    await session.commit()
    return user.message_count


def should_assign_badge(user: TrustedUser) -> bool:
    count = user.message_count
    if count < 10:
        return False
    if count == 10:
        return True
    if (count - 10) % 50 != 0:
        return False
    if user.last_badge_at is not None:
        days_since = (datetime.datetime.now(datetime.UTC) - user.last_badge_at).days
        if days_since < 30:
            return False
    return True


async def update_badge(session: AsyncSession, user_id: int, badge: str) -> None:
    user = await session.get(TrustedUser, user_id)
    if user:
        user.badge = badge
        user.last_badge_at = datetime.datetime.now(datetime.UTC)
        await session.commit()
