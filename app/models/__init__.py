"""
Import all models here so that Alembic's autogenerate can discover them.
"""
from app.database.base import Base  # noqa: F401 — keeps Base importable from models
from app.models.user import User, user_roles_table  # noqa: F401
from app.models.role import Role  # noqa: F401
from app.models.dns_request import DNSRequest, DNSRequestRecord  # noqa: F401
from app.models.approval import Approval  # noqa: F401
from app.models.audit_log import AuditLog  # noqa: F401
from app.models.application_settings import BlacklistedDomain, ApplicationSetting  # noqa: F401
from app.models.enums import (  # noqa: F401
    RequestStatus,
    RequestAction,
    DNSRecordType,
    ApprovalAction,
    RoleName,
)

__all__ = [
    "Base",
    "User",
    "Role",
    "user_roles_table",
    "DNSRequest",
    "DNSRequestRecord",
    "Approval",
    "AuditLog",
    "BlacklistedDomain",
    "ApplicationSetting",
    "RequestStatus",
    "RequestAction",
    "DNSRecordType",
    "ApprovalAction",
    "RoleName",
]
