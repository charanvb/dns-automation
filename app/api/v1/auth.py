"""
Auth routes: login page, register page, logout.

These are web-facing routes that serve Jinja2 HTML pages and set/clear
the JWT cookie on form submission.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.exceptions import AppError
from app.security.dependencies import get_optional_user
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])
templates = Jinja2Templates(directory="app/templates")


def _flash(request: Request, message: str, category: str = "info") -> None:
    if "flash" not in request.session:
        request.session["flash"] = []
    request.session["flash"].append({"message": message, "category": category})


# ── Login ─────────────────────────────────────────────────────────────────────

@router.get("/login", response_class=HTMLResponse)
async def login_page(
    request: Request,
    current_user=Depends(get_optional_user),
):
    if current_user and current_user.is_active:
        return RedirectResponse("/dashboard", status_code=302)
    return templates.TemplateResponse(
        "auth/login.html",
        {"request": request, "current_user": None},
    )


@router.post("/login", response_class=HTMLResponse)
async def login_submit(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    db: AsyncSession = Depends(get_db),
):
    svc = AuthService(db)
    ip = request.client.host if request.client else None
    try:
        user, token = await svc.authenticate(email, password, ip_address=ip)
    except AppError as exc:
        return templates.TemplateResponse(
            "auth/login.html",
            {"request": request, "current_user": None, "error": exc.detail},
            status_code=400,
        )

    response = RedirectResponse("/dashboard", status_code=303)
    cookie = svc.build_cookie_params(token)
    response.set_cookie(**cookie)
    return response


# ── Register ──────────────────────────────────────────────────────────────────

@router.get("/register", response_class=HTMLResponse)
async def register_page(
    request: Request,
    current_user=Depends(get_optional_user),
):
    if current_user and current_user.is_active:
        return RedirectResponse("/dashboard", status_code=302)
    return templates.TemplateResponse(
        "auth/register.html",
        {"request": request, "current_user": None},
    )


@router.post("/register", response_class=HTMLResponse)
async def register_submit(
    request: Request,
    email: str = Form(...),
    full_name: str = Form(...),
    password: str = Form(...),
    password_confirm: str = Form(...),
    department: str = Form(default=""),
    db: AsyncSession = Depends(get_db),
):
    errors: list[str] = []

    # Basic password checks before hitting the service
    if len(password) < 10:
        errors.append("Password must be at least 10 characters.")
    if password != password_confirm:
        errors.append("Passwords do not match.")

    if errors:
        return templates.TemplateResponse(
            "auth/register.html",
            {
                "request": request,
                "current_user": None,
                "errors": errors,
                "form": {"email": email, "full_name": full_name, "department": department},
            },
            status_code=400,
        )

    svc = AuthService(db)
    ip = request.client.host if request.client else None
    try:
        await svc.register(
            email=email,
            full_name=full_name,
            password=password,
            department=department or None,
            ip_address=ip,
        )
    except AppError as exc:
        return templates.TemplateResponse(
            "auth/register.html",
            {
                "request": request,
                "current_user": None,
                "errors": [exc.detail],
                "form": {"email": email, "full_name": full_name, "department": department},
            },
            status_code=400,
        )

    _flash(request, "Registration submitted. An administrator will activate your account shortly.", "success")
    return RedirectResponse("/auth/login", status_code=303)


# ── Logout ────────────────────────────────────────────────────────────────────

@router.post("/logout")
async def logout(request: Request):
    from app.config import get_settings
    settings = get_settings()
    response = RedirectResponse("/auth/login", status_code=303)
    response.delete_cookie(
        key="access_token",
        httponly=True,
        samesite="strict",
        secure=settings.is_production,
    )
    return response
