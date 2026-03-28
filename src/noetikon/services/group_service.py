from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from noetikon.models.group import TelegramGroup


async def get_group(session: AsyncSession, group_id: int) -> TelegramGroup | None:
    result = await session.execute(select(TelegramGroup).where(TelegramGroup.group_id == group_id))
    return result.scalar_one_or_none()


async def get_group_by_id(session: AsyncSession, pk: int) -> TelegramGroup | None:
    return await session.get(TelegramGroup, pk)


async def get_all_groups(session: AsyncSession) -> list[TelegramGroup]:
    result = await session.execute(select(TelegramGroup).order_by(TelegramGroup.title))
    return list(result.scalars().all())


async def create_group(session: AsyncSession, group_id: int, title: str) -> TelegramGroup:
    group = TelegramGroup(group_id=group_id, title=title)
    session.add(group)
    await session.commit()
    await session.refresh(group)
    return group


async def update_group(session: AsyncSession, pk: int, **kwargs) -> TelegramGroup | None:
    group = await session.get(TelegramGroup, pk)
    if group is None:
        return None
    for key, value in kwargs.items():
        setattr(group, key, value)
    await session.commit()
    await session.refresh(group)
    return group


async def get_or_create_group(session: AsyncSession, group_id: int, title: str) -> TelegramGroup:
    group = await get_group(session, group_id)
    if group is None:
        group = await create_group(session, group_id, title)
    return group
