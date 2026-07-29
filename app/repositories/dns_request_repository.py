from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import UUID

from sqlalchemy import func, select

from app.models.dns_request import DNSRequest
from app.models.enums import RequestStatus
from app.repositories.base import BaseRepository


class DNSRequestRepository(BaseRepository[DNSRequest]):
    model = DNSRequest

    async def get_by_request_number(self, request_number: str) -> DNSRequest | None:
        result = await self.db.execute(
            select(DNSRequest).where(DNSRequest.request_number == request_number)
        )
        return result.scalar_one_or_none()

    async def list_for_user(
        self,
        user_id: UUID | str,
        limit: int = 50,
        offset: int = 0,
    ) -> list[DNSRequest]:
        result = await self.db.execute(
            select(DNSRequest)
            .where(DNSRequest.requester_id == user_id)
            .order_by(DNSRequest.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(result.scalars().all())

    async def list_pending_approval(self) -> list[DNSRequest]:
        result = await self.db.execute(
            select(DNSRequest)
            .where(DNSRequest.status == RequestStatus.PENDING_APPROVAL)
            .order_by(DNSRequest.submitted_at.asc())
        )
        return list(result.scalars().all())

    async def count_requests_in_period(
        self,
        user_id: UUID | str,
        hours: int,
    ) -> int:
        since = datetime.now(tz=timezone.utc) - timedelta(hours=hours)
        result = await self.db.execute(
            select(func.count())
            .select_from(DNSRequest)
            .where(
                DNSRequest.requester_id == user_id,
                DNSRequest.created_at >= since,
                DNSRequest.status.notin_(
                    [RequestStatus.DRAFT, RequestStatus.CANCELLED]
                ),
            )
        )
        return result.scalar_one()

    async def generate_request_number(self) -> str:
        """Generate next sequential request number: DNS-YYYY-NNNN."""
        year = datetime.now(tz=timezone.utc).year
        result = await self.db.execute(
            select(func.count())
            .select_from(DNSRequest)
            .where(DNSRequest.request_number.like(f"DNS-{year}-%"))
        )
        seq = result.scalar_one() + 1
        return f"DNS-{year}-{seq:04d}"

    async def count_by_status(self) -> dict[str, int]:
        result = await self.db.execute(
            select(DNSRequest.status, func.count().label("cnt"))
            .group_by(DNSRequest.status)
        )
        return {row.status: row.cnt for row in result.all()}
