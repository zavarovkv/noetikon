import datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from noetikon.models.stats import LLMUsage


async def get_daily_request_count(session: AsyncSession, group_id: int) -> int:
    today = datetime.datetime.now(datetime.UTC).replace(hour=0, minute=0, second=0, microsecond=0)
    result = await session.execute(
        select(func.count()).where(LLMUsage.group_id == group_id, LLMUsage.created_at >= today)
    )
    return result.scalar_one()


async def record_usage(
    session: AsyncSession,
    group_id: int,
    tg_user_id: int,
    input_tokens: int,
    output_tokens: int,
) -> None:
    usage = LLMUsage(
        group_id=group_id,
        tg_user_id=tg_user_id,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
    )
    session.add(usage)
    await session.commit()


async def get_stats(session: AsyncSession, group_id: int, days: int = 30) -> dict:
    since = datetime.datetime.now(datetime.UTC) - datetime.timedelta(days=days)
    result = await session.execute(
        select(
            func.count().label("total_requests"),
            func.coalesce(func.sum(LLMUsage.input_tokens), 0).label("total_input_tokens"),
            func.coalesce(func.sum(LLMUsage.output_tokens), 0).label("total_output_tokens"),
        ).where(LLMUsage.group_id == group_id, LLMUsage.created_at >= since)
    )
    row = result.one()
    return {
        "total_requests": row.total_requests,
        "total_input_tokens": row.total_input_tokens,
        "total_output_tokens": row.total_output_tokens,
        "days": days,
    }


async def get_all_stats(session: AsyncSession, days: int = 30) -> dict:
    since = datetime.datetime.now(datetime.UTC) - datetime.timedelta(days=days)
    result = await session.execute(
        select(
            func.count().label("total_requests"),
            func.coalesce(func.sum(LLMUsage.input_tokens), 0).label("total_input_tokens"),
            func.coalesce(func.sum(LLMUsage.output_tokens), 0).label("total_output_tokens"),
        ).where(LLMUsage.created_at >= since)
    )
    row = result.one()
    return {
        "total_requests": row.total_requests,
        "total_input_tokens": row.total_input_tokens,
        "total_output_tokens": row.total_output_tokens,
        "days": days,
    }
