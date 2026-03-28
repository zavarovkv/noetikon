from fastapi import APIRouter, Form, Request
from fastapi.responses import RedirectResponse

from noetikon.admin.deps import templates
from noetikon.database import async_session
from noetikon.services import group_service

router = APIRouter()


@router.get("")
async def group_list(request: Request):
    async with async_session() as session:
        groups = await group_service.get_all_groups(session)
    return templates.TemplateResponse("groups/list.html", {"request": request, "groups": groups})


@router.get("/{group_pk}/edit")
async def group_edit(request: Request, group_pk: int):
    async with async_session() as session:
        group = await group_service.get_group_by_id(session, group_pk)
    if group is None:
        return RedirectResponse(url="/groups", status_code=302)
    return templates.TemplateResponse("groups/form.html", {"request": request, "group": group})


@router.post("/{group_pk}/edit")
async def group_update(
    request: Request,
    group_pk: int,
    title: str = Form(),
    llm_rate_limit: int = Form(50),
    humor_frequency: int = Form(30),
    is_active: bool = Form(False),
):
    async with async_session() as session:
        await group_service.update_group(
            session,
            group_pk,
            title=title,
            llm_rate_limit=llm_rate_limit,
            humor_frequency=humor_frequency,
            is_active=is_active,
        )
    return RedirectResponse(url="/groups", status_code=302)
