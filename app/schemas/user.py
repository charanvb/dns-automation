from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr


class UserOut(BaseModel):
    id: uuid.UUID
    email: EmailStr
    full_name: str
    department: str | None
    is_active: bool
    is_whitelisted: bool
    is_superuser: bool
    role_names: list[str]
    created_at: datetime
    last_login: datetime | None

    model_config = {"from_attributes": True}
