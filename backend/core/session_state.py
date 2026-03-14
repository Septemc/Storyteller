from __future__ import annotations

import time
import uuid
from dataclasses import dataclass
from typing import Optional

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ..db import models
from .tenant import owner_only


@dataclass
class SessionStateConflictError(Exception):
    session_id: str
    owner_user_id: Optional[str]

    def __str__(self) -> str:
        if self.owner_user_id:
            return f"session_id '{self.session_id}' belongs to another user scope"
        return f"session_id '{self.session_id}' already exists in a different scope"


def build_unique_session_id(user_id: Optional[str] = None) -> str:
    timestamp = int(time.time() * 1000)
    time_suffix = time.strftime("%H%M%S")
    random_suffix = uuid.uuid4().hex[:8]
    session_id = f"S_{timestamp}_{time_suffix}_{random_suffix}"
    if user_id:
        session_id = f"{session_id}_{str(user_id)[:8]}"
    return session_id


def _same_scope(row: models.SessionState, user_id: Optional[str]) -> bool:
    return row.user_id == user_id


def ensure_session_state(
    db: Session,
    session_id: str,
    user_id: Optional[str] = None,
) -> models.SessionState:
    scoped_query = owner_only(
        db.query(models.SessionState).filter(models.SessionState.session_id == session_id),
        models.SessionState,
        user_id,
    )
    state = scoped_query.first()
    if state:
        if user_id and not state.user_id:
            state.user_id = user_id
            db.commit()
            db.refresh(state)
        return state

    existing = db.query(models.SessionState).filter(models.SessionState.session_id == session_id).first()
    if existing:
        existing_owner = getattr(existing, 'user_id', None)
        if existing_owner == user_id:
            return existing
        if existing_owner is None and user_id is not None:
            existing.user_id = user_id
            db.commit()
            db.refresh(existing)
            return existing
        if user_id is None and existing_owner is None:
            return existing
        raise SessionStateConflictError(session_id=session_id, owner_user_id=existing_owner)

    state = models.SessionState(
        session_id=session_id,
        current_dungeon_id=None,
        current_node_id=None,
        total_word_count=0,
        user_id=user_id,
    )
    db.add(state)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        existing = db.query(models.SessionState).filter(models.SessionState.session_id == session_id).first()
        if existing and _same_scope(existing, user_id):
            return existing
        raise SessionStateConflictError(
            session_id=session_id,
            owner_user_id=existing.user_id if existing else None,
        )
    db.refresh(state)
    return state
