"""
UserService — admin operations on user accounts.
"""
from __future__ import annotations

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.exceptions import NotFoundError
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.services.audit_service import AuditService


class UserService:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db
        self._users = UserRepository(db)
        self._audit = AuditService(db)

    async def activate(self, user_id: UUID | str, admin: User) -> User:
        user = await self._users.get_by_id(user_id)
        if user is None:
            raise NotFoundError(f"User {user_id} not found.")
        old = {"is_active": user.is_active}
        user.is_active = True
        await self._db.flush()
        await self._audit.log(
            "user.activated",
            user_id=admin.id,
            resource_type="user",
            resource_id=str(user.id),
            old_value=old,
            new_value={"is_active": True},
        )
        return user

    async def deactivate(self, user_id: UUID | str, admin: User) -> User:
        user = await self._users.get_by_id(user_id)
        if user is None:
            raise NotFoundError(f"User {user_id} not found.")
        old = {"is_active": user.is_active}
        user.is_active = False
        await self._db.flush()
        await self._audit.log(
            "user.deactivated",
            user_id=admin.id,
            resource_type="user",
            resource_id=str(user.id),
            old_value=old,
            new_value={"is_active": False},
        )
        return user

    async def set_whitelist(
        self, user_id: UUID | str, whitelisted: bool, admin: User
    ) -> User:
        user = await self._users.get_by_id(user_id)
        if user is None:
            raise NotFoundError(f"User {user_id} not found.")
        old = {"is_whitelisted": user.is_whitelisted}
        user.is_whitelisted = whitelisted
        await self._db.flush()
        await self._audit.log(
            "user.whitelist_updated",
            user_id=admin.id,
            resource_type="user",
            resource_id=str(user.id),
            old_value=old,
            new_value={"is_whitelisted": whitelisted},
        )
        return user

    async def assign_role(
        self, user_id: UUID | str, role_name: str, admin: User
    ) -> User:
        user = await self._users.get_by_id(user_id)
        if user is None:
            raise NotFoundError(f"User {user_id} not found.")
        role = await self._users.get_role_by_name(role_name)
        if role is None:
            raise NotFoundError(f"Role '{role_name}' not found.")
        await self._users.assign_role(user, role)
        await self._audit.log(
            "user.role_assigned",
            user_id=admin.id,
            resource_type="user",
            resource_id=str(user.id),
            new_value={"role": role_name},
        )
        return user

    async def list_all(self) -> list[User]:
        return await self._users.list_all()

    async def list_pending(self) -> list[User]:
        return await self._users.list_pending_activation()
