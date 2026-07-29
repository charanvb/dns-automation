"""
FastAPI application factory.

Startup sequence:
1. Configure logging
2. Test database connectivity
3. Seed default roles and admin user (idempotent)
4. Start serving

Run with:
    uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
"""
from __future__ import annotations

import logging

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware

from app.config import get_settings
from app.exceptions import AppError, ForbiddenError, UnauthorizedError
from app.utils.logging import configure_logging

configure_logging()
logger = logging.getLogger(__name__)
settings = get_settings()


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.APP_NAME,
        version="1.0.0",
        docs_url="/api/docs" if settings.DEBUG else None,
        redoc_url=None,
        openapi_url="/api/openapi.json" if settings.DEBUG else None,
    )

    # ── Middleware ────────────────────────────────────────────────────────
    app.add_middleware(
        SessionMiddleware,
        secret_key=settings.SECRET_KEY,
        same_site="strict",
        https_only=settings.is_production,
        max_age=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )

    # ── Static files ──────────────────────────────────────────────────────
    app.mount("/static", StaticFiles(directory="app/static"), name="static")

    # ── Routers ───────────────────────────────────────────────────────────
    from app.api.v1 import auth, dashboard, admin, dns_requests

    app.include_router(auth.router)
    app.include_router(dashboard.router)
    app.include_router(dns_requests.router)
    app.include_router(admin.router)

    # ── Exception handlers ────────────────────────────────────────────────
    templates = Jinja2Templates(directory="app/templates")

    @app.exception_handler(UnauthorizedError)
    async def unauthorized_handler(request: Request, exc: UnauthorizedError):
        return RedirectResponse(f"/auth/login?next={request.url.path}", status_code=302)

    @app.exception_handler(ForbiddenError)
    async def forbidden_handler(request: Request, exc: ForbiddenError):
        return templates.TemplateResponse(
            "errors/403.html",
            {"request": request, "detail": exc.detail},
            status_code=403,
        )

    @app.exception_handler(AppError)
    async def app_error_handler(request: Request, exc: AppError):
        return templates.TemplateResponse(
            "errors/500.html",
            {"request": request, "detail": exc.detail},
            status_code=exc.status_code,
        )

    @app.exception_handler(404)
    async def not_found_handler(request: Request, exc):
        return templates.TemplateResponse(
            "errors/404.html",
            {"request": request},
            status_code=404,
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception):
        logger.exception("Unhandled exception on %s %s", request.method, request.url.path)
        try:
            return templates.TemplateResponse(
                "errors/500.html",
                {"request": request, "detail": str(exc)},
                status_code=500,
            )
        except Exception:
            from fastapi.responses import HTMLResponse
            return HTMLResponse(f"Internal Server Error: {exc}", status_code=500)

    # ── Startup ───────────────────────────────────────────────────────────
    @app.on_event("startup")
    async def on_startup():
        logger.info("Starting %s (%s)", settings.APP_NAME, settings.APP_ENV)
        await _seed_initial_data()
        logger.info("Application ready.")

    # ── Shutdown ──────────────────────────────────────────────────────────
    @app.on_event("shutdown")
    async def on_shutdown():
        from app.micetro.client import micetro_client
        await micetro_client.close()
        logger.info("Application shutdown complete.")

    return app


async def _seed_initial_data() -> None:
    """
    Idempotently create default roles and the bootstrap admin user.
    Uses a direct table insert for user_roles to avoid relationship
    complexity with transient objects during seeding.
    """
    from sqlalchemy import select

    from app.database.session import AsyncSessionLocal
    from app.models.role import Role
    from app.models.user import User, user_roles_table
    from app.security.password import hash_password

    async with AsyncSessionLocal() as db:
        try:
            # 1. Seed default roles (idempotent)
            role_map: dict[str, Role] = {}
            for role_name, description in [
                ("admin", "Full portal access and user management."),
                ("approver", "Review and approve or reject DNS change requests."),
                ("requester", "Submit DNS change requests (requires whitelist)."),
            ]:
                result = await db.execute(select(Role).where(Role.name == role_name))
                role = result.scalar_one_or_none()
                if role is None:
                    role = Role(name=role_name, description=description)
                    db.add(role)
                    logger.info("Created role: %s", role_name)
                role_map[role_name] = role

            await db.flush()  # persist roles, ensuring their UUIDs are set

            # 2. Seed bootstrap admin if no users exist
            result = await db.execute(select(User).limit(1))
            if result.scalar_one_or_none() is None:
                admin = User(
                    email=settings.INITIAL_ADMIN_EMAIL.lower(),
                    full_name=settings.INITIAL_ADMIN_FULL_NAME,
                    hashed_password=hash_password(settings.INITIAL_ADMIN_PASSWORD),
                    is_active=True,
                    is_whitelisted=True,
                    is_superuser=True,
                )
                db.add(admin)
                await db.flush()  # get admin.id before inserting into user_roles

                # Direct insert avoids any relationship ambiguity during seeding
                admin_role = role_map.get("admin")
                if admin_role:
                    await db.execute(
                        user_roles_table.insert().values(
                            user_id=admin.id,
                            role_id=admin_role.id,
                        )
                    )
                logger.info("Created bootstrap admin: %s", settings.INITIAL_ADMIN_EMAIL)

            await db.commit()
            logger.info("Seed data applied successfully.")
        except Exception:
            await db.rollback()
            logger.exception("Seed data failed — continuing startup anyway.")


app = create_app()
