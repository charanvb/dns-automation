"""
Admin routes: user management, approval queue.
"""
from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.exceptions import AppError
from app.models.user import User
from app.repositories.dns_request_repository import DNSRequestRepository
from app.security.dependencies import require_admin
from app.services.user_service import UserService

router = APIRouter(prefix="/admin", tags=["admin"])
templates = Jinja2Templates(directory="app/templates")


def _flash(request: Request, message: str, category: str = "info") -> None:
    if "flash" not in request.session:
        request.session["flash"] = []
    request.session["flash"].append({"message": message, "category": category})


# ── User management ───────────────────────────────────────────────────────────

@router.get("/users", response_class=HTMLResponse)
async def admin_users(
    request: Request,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    svc = UserService(db)
    users = await svc.list_all()
    return templates.TemplateResponse(
        "admin/users.html",
        {"request": request, "current_user": admin, "users": users},
    )


@router.post("/users/{user_id}/activate")
async def activate_user(
    user_id: UUID,
    request: Request,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    svc = UserService(db)
    try:
        await svc.activate(user_id, admin)
        _flash(request, "User account activated.", "success")
    except AppError as exc:
        _flash(request, exc.detail, "danger")
    return RedirectResponse("/admin/users", status_code=303)


@router.post("/users/{user_id}/deactivate")
async def deactivate_user(
    user_id: UUID,
    request: Request,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    svc = UserService(db)
    try:
        await svc.deactivate(user_id, admin)
        _flash(request, "User account deactivated.", "warning")
    except AppError as exc:
        _flash(request, exc.detail, "danger")
    return RedirectResponse("/admin/users", status_code=303)


@router.post("/users/{user_id}/whitelist")
async def whitelist_user(
    user_id: UUID,
    request: Request,
    whitelisted: bool = Form(...),
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    svc = UserService(db)
    try:
        await svc.set_whitelist(user_id, whitelisted, admin)
        state = "granted" if whitelisted else "revoked"
        _flash(request, f"DNS request access {state}.", "success")
    except AppError as exc:
        _flash(request, exc.detail, "danger")
    return RedirectResponse("/admin/users", status_code=303)


@router.post("/users/{user_id}/role")
async def assign_role(
    user_id: UUID,
    request: Request,
    role_name: str = Form(...),
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    svc = UserService(db)
    try:
        await svc.assign_role(user_id, role_name, admin)
        _flash(request, f"Role '{role_name}' assigned.", "success")
    except AppError as exc:
        _flash(request, exc.detail, "danger")
    return RedirectResponse("/admin/users", status_code=303)


# ── Approval queue (placeholder — Module 4 will expand this) ─────────────────

@router.get("/approvals", response_class=HTMLResponse)
async def approval_queue(
    request: Request,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    dns_repo = DNSRequestRepository(db)
    pending = await dns_repo.list_pending_approval()
    return templates.TemplateResponse(
        "admin/approvals.html",
        {"request": request, "current_user": admin, "pending_requests": pending},
    )
