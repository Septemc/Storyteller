from __future__ import annotations

import uuid
from typing import Any, Optional

from sqlalchemy import or_
from sqlalchemy.orm import Query, Session


def current_user_id(current_user: Optional[Any]) -> Optional[str]:
    return getattr(current_user, "user_id", None) if current_user else None


def owner_only(query: Query, model: Any, user_id: Optional[str]) -> Query:
    if not hasattr(model, "user_id"):
        return query
    col = getattr(model, "user_id")
    if user_id is None:
        return query.filter(col.is_(None))
    return query.filter(col == user_id)


def owner_or_public(query: Query, model: Any, user_id: Optional[str]) -> Query:
    if not hasattr(model, "user_id"):
        return query
    col = getattr(model, "user_id")
    if user_id is None:
        return query.filter(col.is_(None))
    return query.filter(or_(col == user_id, col.is_(None)))


def resolve_scoped_id(
    db: Session,
    model: Any,
    id_field: str,
    preferred_id: str,
    user_id: Optional[str],
) -> str:
    id_col = getattr(model, id_field)
    existing = db.query(model).filter(id_col == preferred_id).first()
    if not existing:
        return preferred_id

    existing_owner = getattr(existing, "user_id", None)
    if existing_owner == user_id:
        return preferred_id

    owner_part = user_id or "public"
    candidate = f"{preferred_id}__{owner_part}"
    while db.query(model).filter(id_col == candidate).first():
        candidate = f"{preferred_id}__{owner_part}_{uuid.uuid4().hex[:6]}"
    return candidate


def scoped_default_id(base_id: str, user_id: Optional[str]) -> str:
    if user_id:
        return f"{base_id}__{user_id}"
    return base_id
