from __future__ import annotations

import enum
import uuid


def generate_worldbook_id() -> str:
    return f"W{uuid.uuid4().hex[:7]}"


class UserRole(enum.Enum):
    ADMIN = "admin"
    USER = "user"
