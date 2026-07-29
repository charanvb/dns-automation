from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.database.base import Base
from app.models.enums import DNSRecordType, RequestAction, RequestStatus


class DNSRequest(Base):
    __tablename__ = "dns_requests"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    # Human-readable reference, e.g. DNS-2024-0001
    request_number: Mapped[str] = mapped_column(
        String(20), unique=True, nullable=False, index=True
    )
    requester_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )

    # Core fields
    action: Mapped[str] = mapped_column(String(20), nullable=False)  # RequestAction
    zone_name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    status: Mapped[str] = mapped_column(
        String(30), nullable=False, default=RequestStatus.DRAFT, index=True
    )

    # Business metadata
    business_justification: Mapped[str] = mapped_column(Text, nullable=False)
    change_ticket: Mapped[str | None] = mapped_column(String(50), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Scheduling
    scheduled_date: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

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
    submitted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    implemented_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Micetro reference (set after implementation)
    micetro_ref: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # ── Relationships ─────────────────────────────────────────────────────
    requester: Mapped["User"] = relationship(  # type: ignore[name-defined]
        "User",
        back_populates="dns_requests",
        foreign_keys=[requester_id],
        lazy="selectin",
    )
    records: Mapped[list["DNSRequestRecord"]] = relationship(
        "DNSRequestRecord",
        back_populates="request",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    approvals: Mapped[list["Approval"]] = relationship(  # type: ignore[name-defined]
        "Approval",
        back_populates="request",
        cascade="all, delete-orphan",
        order_by="Approval.acted_at",
    )

    def __repr__(self) -> str:
        return f"<DNSRequest {self.request_number} ({self.status})>"


class DNSRequestRecord(Base):
    """One DNS record row within a request. A single request may have many rows."""

    __tablename__ = "dns_request_records"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    request_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("dns_requests.id", ondelete="CASCADE"),
        nullable=False,
    )

    # Per-record action (usually same as parent request action)
    action: Mapped[str] = mapped_column(String(20), nullable=False)  # RequestAction

    # DNS record fields
    label: Mapped[str] = mapped_column(String(255), nullable=False)
    record_type: Mapped[str] = mapped_column(String(10), nullable=False)  # DNSRecordType
    ttl: Mapped[int] = mapped_column(Integer, default=300, nullable=False)
    value: Mapped[str] = mapped_column(Text, nullable=False)  # RDATA

    # For Modify / Delete — reference to the existing Micetro record
    existing_micetro_ref: Mapped[str | None] = mapped_column(String(255), nullable=True)
    existing_value: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Validation
    validation_status: Mapped[str] = mapped_column(
        String(20), default="pending", nullable=False
    )
    validation_errors: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # ── Relationships ─────────────────────────────────────────────────────
    request: Mapped["DNSRequest"] = relationship("DNSRequest", back_populates="records")

    def __repr__(self) -> str:
        return f"<DNSRequestRecord {self.label} {self.record_type} {self.value}>"
