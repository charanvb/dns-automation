from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from sqlalchemy import DateTime, String

from app.database.base import Base
from app.models.user import User, user_roles_table


class Role(Base):
    __tablename__ = "roles"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    users: Mapped[list["User"]] = relationship(  # type: ignore[name-defined]
        "User",
        secondary=user_roles_table,
        # mirror of User.roles: explicit secondaryjoin to avoid assigned_by ambiguity
        secondaryjoin=lambda: User.id == user_roles_table.c.user_id,
        back_populates="roles",
    )

    def __repr__(self) -> str:
        return f"<Role {self.name}>"
