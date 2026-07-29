"""
AuditService — write-only service for recording events.
Uses fire-and-forget pattern: never raises, always logs errors.
"""
from __future__ import annotations

import logging
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit_log import AuditLog
from app.repositories.audit_repository import AuditRepository

logger = logging.getLogger(__name__)


class AuditService:
    def __init__(self, db: AsyncSession) -> None:
        self._repo = AuditRepository(db)

    async def log(
        self,
        action: str,
        *,
        user_id: UUID | str | None = None,
        resource_type: str | None = None,
        resource_id: str | None = None,
        old_value: dict | None = None,
        new_value: dict | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> None:
        try:
            entry = AuditLog(
                user_id=user_id,
                action=action,
                resource_type=resource_type,
                resource_id=str(resource_id) if resource_id else None,
                old_value=old_value,
                new_value=new_value,
                ip_address=ip_address,
                user_agent=user_agent,
            )
            await self._repo.create(entry)
        except Exception:
            logger.exception("Failed to write audit log for action=%s", action)
