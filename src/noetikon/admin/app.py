import uvicorn
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

from noetikon.admin.auth import AuthMiddleware
from noetikon.admin.routes import groups, login, stats, users
from noetikon.config import get_settings


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title="Noetikon Admin", docs_url=None, redoc_url=None)

    app.add_middleware(SessionMiddleware, secret_key=settings.admin_password)
    app.add_middleware(AuthMiddleware)

    app.include_router(login.router)
    app.include_router(users.router, prefix="/users")
    app.include_router(groups.router, prefix="/groups")
    app.include_router(stats.router, prefix="/stats")

    return app


def main():
    settings = get_settings()
    app = create_app()
    uvicorn.run(app, host="0.0.0.0", port=settings.admin_port)


if __name__ == "__main__":
    main()
