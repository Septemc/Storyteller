from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from ....core import orchestrator
from ....core.auth import User as AuthUser, get_current_user_sync
from ....core.tenant import current_user_id, owner_only
from ....db import models
from ....db.base import get_db
from ....modules.agent.services.log_store import load_segment_logs
from .schemas import RecentSegmentsResponse, StorySegmentItem, UpdateFrontendDurationRequest, UpdateSegmentRequest

router = APIRouter()


@router.get("/story/recent", response_model=RecentSegmentsResponse)
def get_recent_segments(session_id: str = Query(..., description="session id"), limit: int = Query(5, description="segment limit"), db: Session = Depends(get_db), current_user: Optional[AuthUser] = Depends(get_current_user_sync)) -> RecentSegmentsResponse:
    user_id = current_user_id(current_user)
    segments = owner_only(db.query(models.StorySegment).filter(models.StorySegment.session_id == session_id), models.StorySegment, user_id).order_by(models.StorySegment.order_index.desc()).limit(limit).all()
    segments.reverse()
    log_map = load_segment_logs(db, session_id, user_id)
    payload = [StorySegmentItem(segment_id=seg.segment_id, order_index=seg.order_index, user_input=seg.user_input, text=seg.text, agent_public_log=(log_map.get(seg.segment_id) or {}).get("publicLog"), agent_dev_log=(log_map.get(seg.segment_id) or {}).get("developerLog"), paragraph_word_count=seg.paragraph_word_count or 0, cumulative_word_count=seg.cumulative_word_count or 0, frontend_duration=seg.frontend_duration or 0.0, backend_duration=seg.backend_duration or 0.0, created_at=seg.created_at.isoformat() if seg.created_at else None) for seg in segments]
    return RecentSegmentsResponse(segments=payload)


@router.post("/story/update_frontend_duration")
def update_frontend_duration(req: UpdateFrontendDurationRequest, db: Session = Depends(get_db), current_user: Optional[AuthUser] = Depends(get_current_user_sync)):
    user_id = current_user_id(current_user)
    segment = owner_only(db.query(models.StorySegment).filter(models.StorySegment.segment_id == req.segment_id), models.StorySegment, user_id).first()
    if not segment:
        return {"success": False, "message": "Segment not found"}
    segment.frontend_duration = req.frontend_duration
    db.commit()
    return {"success": True}


@router.post("/story/update_segment")
def update_segment(req: UpdateSegmentRequest, db: Session = Depends(get_db), current_user: Optional[AuthUser] = Depends(get_current_user_sync)):
    user_id = current_user_id(current_user)
    segment = owner_only(db.query(models.StorySegment).filter(models.StorySegment.segment_id == req.segment_id), models.StorySegment, user_id).first()
    if not segment:
        return {"success": False, "message": "Segment not found"}
    parts = orchestrator.extract_story_parts(req.text)
    segment.text = req.text
    segment.content_thinking = parts["thinking"]
    segment.content_story = parts["story"]
    segment.content_summary = parts["summary"]
    segment.content_actions = parts["actions"]
    segment.paragraph_word_count = len(parts["story"]) if parts["story"] else segment.paragraph_word_count
    db.commit()
    return {"success": True, "segment_id": req.segment_id, "extracted": {"has_thinking": parts["thinking"] is not None, "has_story": parts["story"] is not None, "has_summary": parts["summary"] is not None, "has_actions": parts["actions"] is not None, "word_count": segment.paragraph_word_count}}
