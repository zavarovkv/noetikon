from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import RedirectResponse

OPEN_PATHS = {"/login", "/favicon.ico"}


class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if request.url.path in OPEN_PATHS:
            return await call_next(request)

        user = request.session.get("user")
        if not user:
            return RedirectResponse(url="/login", status_code=302)

        return await call_next(request)
