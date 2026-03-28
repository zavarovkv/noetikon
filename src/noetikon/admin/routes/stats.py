from fastapi import APIRouter, Query, Request

from noetikon.admin.deps import templates
from noetikon.database import async_session
from noetikon.services import stats_service

router = APIRouter()


@router.get("")
async def stats_page(request: Request, days: int = Query(30)):
    async with async_session() as session:
        data = await stats_service.get_all_stats(session, days=days)
    return templates.TemplateResponse("stats.html", {"request": request, "stats": data, "days": days})
