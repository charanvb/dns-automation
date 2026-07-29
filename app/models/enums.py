"""
Enums shared across SQLAlchemy models and Pydantic schemas.
Defined here once to avoid circular imports.
"""
from __future__ import annotations

import enum


class RequestStatus(str, enum.Enum):
    DRAFT = "draft"
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    REJECTED = "rejected"
    CANCELLED = "cancelled"
    FAILED = "failed"


class RequestAction(str, enum.Enum):
    CREATE = "create"
    MODIFY = "modify"
    DELETE = "delete"


class DNSRecordType(str, enum.Enum):
    A = "A"
    AAAA = "AAAA"
    CNAME = "CNAME"
    TXT = "TXT"
    PTR = "PTR"
    SRV = "SRV"
    MX = "MX"
    NS = "NS"
    OTHER = "OTHER"


class ApprovalAction(str, enum.Enum):
    APPROVED = "approved"
    REJECTED = "rejected"
    INFO_REQUESTED = "info_requested"


class RoleName(str, enum.Enum):
    ADMIN = "admin"
    APPROVER = "approver"
    REQUESTER = "requester"
