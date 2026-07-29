from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.models.user import User
from app.models.role import Role
from app.repositories.base import BaseRepository


class UserRepository(BaseRepository[User]):
    model = User

    async def get_by_email(self, email: str) -> User | None:
        result = await self.db.execute(
            select(User)
            .where(User.email == email.lower())
            .options(selectinload(User.roles))
        )
        return result.scalar_one_or_none()

    async def get_by_id(self, id: UUID | str) -> User | None:
        result = await self.db.execute(
            select(User)
            .where(User.id == id)
            .options(selectinload(User.roles))
        )
        return result.scalar_one_or_none()

    async def list_all(self, limit: int = 200, offset: int = 0) -> list[User]:
        result = await self.db.execute(
            select(User)
            .options(selectinload(User.roles))
            .order_by(User.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(result.scalars().all())

    async def list_pending_activation(self) -> list[User]:
        result = await self.db.execute(
            select(User)
            .where(User.is_active == False)  # noqa: E712
            .options(selectinload(User.roles))
            .order_by(User.created_at.asc())
        )
        return list(result.scalars().all())

    async def email_exists(self, email: str) -> bool:
        result = await self.db.execute(
            select(User.id).where(User.email == email.lower())
        )
        return result.scalar_one_or_none() is not None

    async def count_all(self) -> int:
        from sqlalchemy import func, select
        result = await self.db.execute(select(func.count()).select_from(User))
        return result.scalar_one()

    async def get_role_by_name(self, name: str) -> Role | None:
        result = await self.db.execute(
            select(Role).where(Role.name == name)
        )
        return result.scalar_one_or_none()

    async def assign_role(self, user: User, role: Role) -> None:
        if role not in user.roles:
            user.roles.append(role)
            await self.db.flush()
