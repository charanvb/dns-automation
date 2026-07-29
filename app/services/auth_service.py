"""
AuthService — registration, login, logout logic.
All password and token operations are handled here; routes stay thin.
"""
from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.exceptions import ConflictError, UnauthorizedError, ForbiddenError
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.security.jwt import COOKIE_NAME, create_access_token
from app.security.password import hash_password, verify_password
from app.services.audit_service import AuditService

settings = get_settings()


class AuthService:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db
        self._users = UserRepository(db)
        self._audit = AuditService(db)

    async def register(
        self,
        email: str,
        full_name: str,
        password: str,
        department: str | None = None,
        ip_address: str | None = None,
    ) -> User:
        """
        Create a new inactive user.
        Account must be activated by an admin before the user can log in.
        """
        email = email.strip().lower()

        if await self._users.email_exists(email):
            raise ConflictError(f"An account with email {email!r} already exists.")

        user = User(
            email=email,
            full_name=full_name.strip(),
            hashed_password=hash_password(password),
            department=department,
            is_active=False,
            is_whitelisted=False,
            is_superuser=False,
        )
        # Assign default 'requester' role
        requester_role = await self._users.get_role_by_name("requester")
        if requester_role:
            user.roles = [requester_role]

        await self._users.create(user)

        await self._audit.log(
            "user.registered",
            user_id=user.id,
            resource_type="user",
            resource_id=str(user.id),
            new_value={"email": email, "full_name": full_name},
            ip_address=ip_address,
        )
        return user

    async def authenticate(
        self,
        email: str,
        password: str,
        ip_address: str | None = None,
    ) -> tuple[User, str]:
        """
        Verify credentials and return (User, jwt_token).
        Raises appropriate errors on failure.
        """
        email = email.strip().lower()
        user = await self._users.get_by_email(email)

        if user is None or not verify_password(password, user.hashed_password):
            raise UnauthorizedError("Invalid email or password.")

        if not user.is_active:
            raise ForbiddenError(
                "Your account is pending activation. "
                "An administrator will review your registration shortly."
            )

        # Update last_login
        user.last_login = datetime.now(tz=timezone.utc)
        await self._db.flush()

        token = create_access_token(subject=str(user.id))

        await self._audit.log(
            "user.login",
            user_id=user.id,
            resource_type="user",
            resource_id=str(user.id),
            ip_address=ip_address,
        )
        return user, token

    def build_cookie_params(self, token: str) -> dict:
        """Return kwargs for response.set_cookie()."""
        return {
            "key": COOKIE_NAME,
            "value": f"Bearer {token}",
            "httponly": True,
            "max_age": settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            "samesite": "strict",
            "secure": settings.is_production,
        }

    def clear_cookie_params(self) -> dict:
        """Return kwargs for response.delete_cookie()."""
        return {
            "key": COOKIE_NAME,
            "httponly": True,
            "samesite": "strict",
            "secure": settings.is_production,
        }
