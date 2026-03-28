from fastapi import APIRouter, Form, Request
from fastapi.responses import RedirectResponse

from noetikon.admin.deps import templates
from noetikon.database import async_session
from noetikon.services import user_registry

router = APIRouter()


@router.get("")
async def user_list(request: Request):
    async with async_session() as session:
        users = await user_registry.get_all_users(session)
    return templates.TemplateResponse("users/list.html", {"request": request, "users": users})


@router.get("/new")
async def user_new(request: Request):
    return templates.TemplateResponse("users/form.html", {"request": request, "user": None})


@router.post("/new")
async def user_create(
    request: Request,
    group_id: int = Form(),
    tg_user_id: int = Form(),
    tg_username: str = Form(""),
    email: str = Form(""),
    is_trusted: bool = Form(True),
):
    async with async_session() as session:
        await user_registry.create_user(
            session,
            group_id=group_id,
            tg_user_id=tg_user_id,
            tg_username=tg_username or None,
            email=email or None,
            is_trusted=is_trusted,
        )
    return RedirectResponse(url="/users", status_code=302)


@router.get("/{user_id}/edit")
async def user_edit(request: Request, user_id: int):
    async with async_session() as session:
        user = await user_registry.get_user_by_id(session, user_id)
    if user is None:
        return RedirectResponse(url="/users", status_code=302)
    return templates.TemplateResponse("users/form.html", {"request": request, "user": user})


@router.post("/{user_id}/edit")
async def user_update(
    request: Request,
    user_id: int,
    tg_username: str = Form(""),
    email: str = Form(""),
    is_trusted: bool = Form(False),
):
    async with async_session() as session:
        await user_registry.update_user(
            session,
            user_id,
            tg_username=tg_username or None,
            email=email or None,
            is_trusted=is_trusted,
        )
    return RedirectResponse(url="/users", status_code=302)


@router.post("/{user_id}/toggle-trust")
async def user_toggle_trust(user_id: int):
    async with async_session() as session:
        user = await user_registry.get_user_by_id(session, user_id)
        if user:
            await user_registry.update_user(session, user_id, is_trusted=not user.is_trusted)
    return RedirectResponse(url="/users", status_code=302)


@router.post("/{user_id}/delete")
async def user_delete(user_id: int):
    async with async_session() as session:
        await user_registry.delete_user(session, user_id)
    return RedirectResponse(url="/users", status_code=302)
