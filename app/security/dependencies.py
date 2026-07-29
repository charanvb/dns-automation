"""
FastAPI dependency functions for authentication and authorisation.
All route handlers that need an authenticated user should declare one of these as a dependency.
"""
from __future__ import annotations

from fastapi import Depends, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.exceptions import ForbiddenError, UnauthorizedError
from app.models.user import User
from app.security.jwt import COOKIE_NAME, get_subject_from_token


# ── Internal helpers ──────────────────────────────────────────────────────────

async def _get_user_from_request(request: Request, db: AsyncSession) -> User | None:
    """Extract and validate the JWT cookie, return the User or None."""
    raw = request.cookies.get(COOKIE_NAME)
    if not raw:
        return None
    token = raw.removeprefix("Bearer ")
    user_id = get_subject_from_token(token)
    if not user_id:
        return None

    from app.repositories.user_repository import UserRepository
    repo = UserRepository(db)
    return await repo.get_by_id(user_id)


# ── Public dependencies ───────────────────────────────────────────────────────

async def get_optional_user(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> User | None:
    """Returns the current user or None — for pages that work for both anon & auth."""
    return await _get_user_from_request(request, db)


async def require_authenticated_user(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> User:
    """Require a valid, active session. Redirects to /auth/login if missing."""
    user = await _get_user_from_request(request, db)
    if user is None:
        raise UnauthorizedError("Authentication required.")
    if not user.is_active:
        raise ForbiddenError("Your account is pending admin approval.")
    return user


async def require_whitelisted_user(
    user: User = Depends(require_authenticated_user),
) -> User:
    """Require the user to be whitelisted (allowed to submit DNS requests)."""
    if not user.is_whitelisted and not user.is_admin:
        raise ForbiddenError("Your account is not yet authorised to submit DNS requests.")
    return user


async def require_approver(
    user: User = Depends(require_authenticated_user),
) -> User:
    """Require approver or admin role."""
    if not user.is_approver:
        raise ForbiddenError("You do not have the Approver role.")
    return user


async def require_admin(
    user: User = Depends(require_authenticated_user),
) -> User:
    """Require admin role."""
    if not user.is_admin:
        raise ForbiddenError("You do not have the Admin role.")
    return user
