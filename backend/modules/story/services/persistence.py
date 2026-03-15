from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy.orm import Session

from ....db import models
from .content_parser import extract_story_parts
from .runtime_context import get_or_create_session_state
from ....core.tenant import owner_only


def persist_story_segment(db: Session, session_id: str, story_text: str, user_input: str = None, paragraph_word_count: int = 0, frontend_duration: float = 0.0, backend_duration: float = 0.0, user_id: Optional[str] = None) -> int:
    state = get_or_create_session_state(db, session_id, user_id=user_id)
    if state and not state.user_id and user_id:
        state.user_id = user_id
        db.commit()
    existing_count = owner_only(db.query(models.StorySegment).filter(models.StorySegment.session_id == session_id), models.StorySegment, user_id).count()
    order_index = existing_count + 1
    last_segment = owner_only(db.query(models.StorySegment).filter(models.StorySegment.session_id == session_id), models.StorySegment, user_id).order_by(models.StorySegment.order_index.desc()).first()
    cumulative_word_count = (last_segment.cumulative_word_count if last_segment else 0) + paragraph_word_count
    segment_id = _build_segment_id(db, session_id, order_index, user_id)
    parts = extract_story_parts(story_text)
    db.add(models.StorySegment(segment_id=segment_id, session_id=session_id, user_id=user_id, order_index=order_index, user_input=user_input, text=story_text, dungeon_id=state.current_dungeon_id, dungeon_node_id=state.current_node_id, paragraph_word_count=paragraph_word_count, cumulative_word_count=cumulative_word_count, frontend_duration=frontend_duration, backend_duration=backend_duration, content_thinking=parts["thinking"], content_story=parts["story"], content_summary=parts["summary"], content_actions=parts["actions"], created_at=datetime.utcnow()))
    state.total_word_count = (state.total_word_count or 0) + paragraph_word_count
    db.commit()
    return order_index


def _build_segment_id(db: Session, session_id: str, order_index: int, user_id: Optional[str]) -> str:
    base_segment_id = f"{session_id}_{order_index}"
    if not db.query(models.StorySegment).filter(models.StorySegment.segment_id == base_segment_id).first():
        return base_segment_id
    owner_part = user_id or "public"
    suffix = 1
    segment_id = f"{base_segment_id}__{owner_part}"
    while db.query(models.StorySegment).filter(models.StorySegment.segment_id == segment_id).first():
        suffix += 1
        segment_id = f"{base_segment_id}__{owner_part}_{suffix}"
    return segment_id
