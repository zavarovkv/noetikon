from fastapi import APIRouter, Form, Request
from fastapi.responses import RedirectResponse

from noetikon.admin.deps import templates
from noetikon.config import get_settings

router = APIRouter()


@router.get("/login")
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request, "error": None})


@router.post("/login")
async def login_submit(request: Request, username: str = Form(), password: str = Form()):
    settings = get_settings()
    if username == settings.admin_username and password == settings.admin_password:
        request.session["user"] = username
        return RedirectResponse(url="/users", status_code=302)
    return templates.TemplateResponse("login.html", {"request": request, "error": "Wrong credentials"})


@router.get("/logout")
async def logout(request: Request):
    request.session.clear()
    return RedirectResponse(url="/login", status_code=302)


@router.get("/")
async def index():
    return RedirectResponse(url="/users", status_code=302)
