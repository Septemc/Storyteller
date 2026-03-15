from __future__ import annotations

from typing import List, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from ....core.auth import User as AuthUser, get_current_user_sync
from ....core.tenant import current_user_id, owner_only
from ....db import models
from ....db.base import get_db
from .helpers import build_branch_info, build_segment_preview, empty_save_detail, save_display_name, save_info_with_branch
from .schemas import SaveDetail, SaveInfo

router = APIRouter()


@router.get("/story/stats")
def get_story_stats(db: Session = Depends(get_db), current_user: Optional[AuthUser] = Depends(get_current_user_sync)):
    user_id = current_user_id(current_user)
    if not user_id:
        return {"stories": 0, "characters": 0, "worldbook": 0, "words": 0}
    story_segments = owner_only(db.query(models.StorySegment), models.StorySegment, user_id).all()
    return {"stories": len(story_segments), "characters": owner_only(db.query(models.Character), models.Character, user_id).count(), "worldbook": owner_only(db.query(models.WorldbookEntry), models.WorldbookEntry, user_id).count(), "words": sum((segment.paragraph_word_count or 0) for segment in story_segments)}


@router.get("/story/saves/list", response_model=List[SaveInfo])
def list_saves(db: Session = Depends(get_db), current_user: Optional[AuthUser] = Depends(get_current_user_sync)):
    user_id = current_user_id(current_user)
    sessions = owner_only(db.query(models.SessionState), models.SessionState, user_id).order_by(models.SessionState.updated_at.desc()).all()
    items: List[SaveInfo] = []
    for session in sessions:
        branch = owner_only(db.query(models.SessionBranch).filter(models.SessionBranch.session_id == session.session_id), models.SessionBranch, user_id).first()
        story = owner_only(db.query(models.StoryRecord).filter(models.StoryRecord.story_id == branch.story_id), models.StoryRecord, user_id).first() if branch else None
        segment_count = owner_only(db.query(models.StorySegment).filter(models.StorySegment.session_id == session.session_id), models.StorySegment, user_id).count()
        items.append(save_info_with_branch(session, branch, story, segment_count))
    return items


@router.get("/story/saves/detail", response_model=SaveDetail)
def get_save_detail(session_id: str = Query(..., description="session id"), db: Session = Depends(get_db), current_user: Optional[AuthUser] = Depends(get_current_user_sync)):
    user_id = current_user_id(current_user)
    session = owner_only(db.query(models.SessionState).filter(models.SessionState.session_id == session_id), models.SessionState, user_id).first()
    if not session:
        return empty_save_detail(session_id)
    branch = owner_only(db.query(models.SessionBranch).filter(models.SessionBranch.session_id == session_id), models.SessionBranch, user_id).first()
    story = owner_only(db.query(models.StoryRecord).filter(models.StoryRecord.story_id == branch.story_id), models.StoryRecord, user_id).first() if branch else None
    segments = owner_only(db.query(models.StorySegment).filter(models.StorySegment.session_id == session_id), models.StorySegment, user_id).order_by(models.StorySegment.order_index).all()
    related_branches = owner_only(db.query(models.SessionBranch).filter(models.SessionBranch.story_id == branch.story_id), models.SessionBranch, user_id).order_by(models.SessionBranch.updated_at.desc()).all() if branch else []
    branch_items = []
    for item in related_branches:
        branch_session = owner_only(db.query(models.SessionState).filter(models.SessionState.session_id == item.session_id), models.SessionState, user_id).first()
        branch_segment_count = owner_only(db.query(models.StorySegment).filter(models.StorySegment.session_id == item.session_id), models.StorySegment, user_id).count()
        branch_items.append(build_branch_info(item, branch_session, segment_count=branch_segment_count, total_word_count=getattr(branch_session, "total_word_count", 0) or 0))
    return SaveDetail(
        session_id=session.session_id,
        display_name=save_display_name(session),
        segment_count=len(segments),
        total_word_count=session.total_word_count or 0,
        story_id=getattr(story, "story_id", None),
        story_title=getattr(story, "title", None),
        branch_id=getattr(branch, "branch_id", None),
        branch_display_name=next((item.display_name for item in branch_items if item.session_id == session.session_id), None),
        branch_type=getattr(branch, "branch_type", None),
        branch_status=getattr(branch, "status", None),
        parent_branch_id=getattr(branch, "parent_branch_id", None),
        reasoning_strength=getattr(branch, "reasoning_strength", None),
        created_at=session.updated_at.isoformat() if session.updated_at else None,
        updated_at=session.updated_at.isoformat() if session.updated_at else None,
        story_branch_count=len(branch_items),
        branches=branch_items,
        segments=[{"index": seg.order_index, "order_index": seg.order_index, "segment_id": seg.segment_id, "preview": build_segment_preview(seg), "word_count": seg.paragraph_word_count or 0, "created_at": seg.created_at.isoformat() if seg.created_at else None} for seg in segments],
    )
