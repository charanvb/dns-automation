from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, String, Table
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.database.base import Base

# ── Many-to-many junction table ──────────────────────────────────────────────
user_roles_table = Table(
    "user_roles",
    Base.metadata,
    Column(
        "user_id",
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "role_id",
        UUID(as_uuid=True),
        ForeignKey("roles.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "assigned_at",
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    ),
    Column(
        "assigned_by",
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    ),
)


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    email: Mapped[str] = mapped_column(
        String(255), unique=True, nullable=False, index=True
    )
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    department: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # Account state
    is_active: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )  # requires admin approval before login is allowed
    is_whitelisted: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )  # can submit DNS change requests
    is_superuser: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
    last_login: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # ── Relationships ─────────────────────────────────────────────────────
    roles: Mapped[list["Role"]] = relationship(  # type: ignore[name-defined]
        "Role",
        secondary=user_roles_table,
        back_populates="users",
        lazy="selectin",
    )
    dns_requests: Mapped[list["DNSRequest"]] = relationship(  # type: ignore[name-defined]
        "DNSRequest",
        back_populates="requester",
        foreign_keys="DNSRequest.requester_id",
    )
    audit_logs: Mapped[list["AuditLog"]] = relationship(  # type: ignore[name-defined]
        "AuditLog", back_populates="user"
    )

    # ── Computed helpers ──────────────────────────────────────────────────
    @property
    def role_names(self) -> list[str]:
        return [r.name for r in self.roles]

    @property
    def is_admin(self) -> bool:
        return self.is_superuser or "admin" in self.role_names

    @property
    def is_approver(self) -> bool:
        return self.is_admin or "approver" in self.role_names

    def __repr__(self) -> str:
        return f"<User {self.email}>"
