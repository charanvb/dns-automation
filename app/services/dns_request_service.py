"""DNS change request service — create, submit, list, and retrieve requests."""
from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.exceptions import AppError
from app.models.dns_request import DNSRequest, DNSRequestRecord
from app.models.enums import RequestStatus
from app.repositories.dns_request_repository import DNSRequestRepository
from app.validation.dns_validators import validate_record

logger = logging.getLogger(__name__)
settings = get_settings()


@dataclass
class RecordInput:
    label: str
    record_type: str
    ttl: int
    value: str


class DNSRequestService:
    def __init__(self, db: AsyncSession) -> None:
        self._repo = DNSRequestRepository(db)
        self._db = db

    async def create(
        self,
        *,
        user,
        action: str,
        zone_name: str,
        business_justification: str,
        change_ticket: str | None,
        notes: str | None,
        records: list[RecordInput],
        submit: bool = False,
    ) -> DNSRequest:
        """Create a DNS request as DRAFT or submit directly for approval."""
        zone_name = zone_name.strip().lower().rstrip(".")

        if not zone_name:
            raise AppError("Zone name is required.")
        if not business_justification.strip():
            raise AppError("Business justification is required.")
        if not records:
            raise AppError("At least one DNS record row is required.")

        # Validate every record before persisting anything
        all_errors: list[str] = []
        for i, rec in enumerate(records, 1):
            if not rec.label.strip():
                all_errors.append(f"Row {i}: Label is required.")
            if not rec.value.strip():
                all_errors.append(f"Row {i}: Value is required.")
            for err in validate_record(rec.record_type, rec.value):
                all_errors.append(f"Row {i}: {err}")
        if all_errors:
            raise AppError("; ".join(all_errors))

        # Rate-limit check only applies when actually submitting (not saving a draft)
        if submit and not user.is_superuser:
            count = await self._repo.count_requests_in_period(
                user.id, settings.RATE_LIMIT_PERIOD_HOURS
            )
            if count >= settings.RATE_LIMIT_REQUESTS:
                raise AppError(
                    f"Rate limit: you may submit at most {settings.RATE_LIMIT_REQUESTS} "
                    f"request(s) per {settings.RATE_LIMIT_PERIOD_HOURS} hours."
                )

        request_number = await self._repo.generate_request_number()
        status = RequestStatus.PENDING_APPROVAL if submit else RequestStatus.DRAFT
        submitted_at = datetime.now(tz=timezone.utc) if submit else None

        dns_request = DNSRequest(
            request_number=request_number,
            requester_id=user.id,
            action=action,
            zone_name=zone_name,
            status=status,
            business_justification=business_justification.strip(),
            change_ticket=change_ticket or None,
            notes=notes or None,
            submitted_at=submitted_at,
        )
        self._db.add(dns_request)
        await self._db.flush()  # get dns_request.id

        for rec in records:
            self._db.add(DNSRequestRecord(
                request_id=dns_request.id,
                action=action,
                label=rec.label.strip(),
                record_type=rec.record_type.upper(),
                ttl=rec.ttl,
                value=rec.value.strip(),
                validation_status="valid",
            ))

        await self._db.commit()
        await self._db.refresh(dns_request)
        logger.info(
            "DNS request %s created by %s (status=%s)",
            dns_request.request_number, user.email, status,
        )
        return dns_request

    async def list_for_user(
        self, user_id: UUID, limit: int = 50, offset: int = 0
    ) -> list[DNSRequest]:
        return await self._repo.list_for_user(user_id, limit=limit, offset=offset)

    async def list_all(self, limit: int = 100, offset: int = 0) -> list[DNSRequest]:
        return await self._repo.list_all(limit=limit, offset=offset)

    async def get_by_id(self, request_id: str | UUID) -> DNSRequest | None:
        return await self._repo.get_by_id(request_id)

    async def approve_or_reject(
        self,
        *,
        request_id: str | UUID,
        approver,
        decision: str,
        comments: str = "",
    ) -> DNSRequest:
        """Approve or reject a pending DNS request and record the approval."""
        from app.models.approval import Approval
        from app.models.enums import ApprovalAction

        dns_req = await self._repo.get_by_id(request_id)
        if dns_req is None:
            raise AppError("Request not found.")
        if dns_req.status != RequestStatus.PENDING_APPROVAL:
            raise AppError(
                f"Cannot act on a request with status '{dns_req.status}'. "
                "Only pending_approval requests can be approved or rejected."
            )
        if decision == "reject" and not comments.strip():
            raise AppError("Rejection comments are required.")

        if decision == "approve":
            action_value = ApprovalAction.APPROVED.value
            new_status = RequestStatus.APPROVED
        elif decision == "reject":
            action_value = ApprovalAction.REJECTED.value
            new_status = RequestStatus.REJECTED
        else:
            raise AppError(f"Invalid decision: '{decision}'.")

        approval = Approval(
            request_id=dns_req.id,
            approver_id=approver.id,
            action=action_value,
            comments=comments.strip() or None,
        )
        self._db.add(approval)
        dns_req.status = new_status

        await self._db.commit()
        await self._db.refresh(dns_req)
        logger.info(
            "DNS request %s %sd by %s", dns_req.request_number, decision, approver.email
        )
        return dns_req
