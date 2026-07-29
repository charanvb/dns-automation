"""
Dashboard route — main landing page after login.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.models.user import User
from app.repositories.dns_request_repository import DNSRequestRepository
from app.repositories.user_repository import UserRepository
from app.security.dependencies import require_authenticated_user

router = APIRouter(tags=["dashboard"])
templates = Jinja2Templates(directory="app/templates")


@router.get("/", response_class=HTMLResponse)
async def root_redirect():
    return RedirectResponse("/dashboard", status_code=302)


@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard(
    request: Request,
    current_user: User = Depends(require_authenticated_user),
    db: AsyncSession = Depends(get_db),
):
    dns_repo = DNSRequestRepository(db)
    user_repo = UserRepository(db)

    my_requests = await dns_repo.list_for_user(current_user.id, limit=5)
    status_counts = await dns_repo.count_by_status()

    ctx: dict = {
        "request": request,
        "current_user": current_user,
        "my_recent_requests": my_requests,
        "status_counts": status_counts,
    }

    # Admin-only stats
    if current_user.is_admin:
        ctx["pending_approval_count"] = status_counts.get("pending_approval", 0)
        ctx["pending_users"] = await user_repo.list_pending_activation()

    return templates.TemplateResponse("dashboard/index.html", ctx)
