from __future__ import annotations

import json
import uuid
from typing import Dict, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from ....core.auth import User as AuthUser, get_current_user_sync
from ....core.session_state import build_unique_session_id
from ....core.tenant import current_user_id, owner_only
from ....db import models
from ....db.base import get_db
from ....modules.agent.services.branch_state import cleanup_branch_story, create_branch_from_session_copy, ensure_story_branch
from ....modules.agent.services.log_store import copy_segment_logs, delete_logs_for_segments, delete_logs_for_session
from .helpers import branch_display_name, load_json
from .schemas import BranchRenameRequest, CopySaveFromSegmentRequest, CreateBranchRequest, DeleteSegmentCascadeRequest, SaveRenameRequest, StoryRenameRequest

router = APIRouter()


@router.post("/story/saves/rename")
def rename_save(req: SaveRenameRequest, db: Session = Depends(get_db), current_user: Optional[AuthUser] = Depends(get_current_user_sync)):
    user_id = current_user_id(current_user)
    return _rename_branch_display_name(db, req.session_id, req.display_name, user_id)


@router.post("/story/stories/rename")
def rename_story(req: StoryRenameRequest, db: Session = Depends(get_db), current_user: Optional[AuthUser] = Depends(get_current_user_sync)):
    user_id = current_user_id(current_user)
    story = owner_only(db.query(models.StoryRecord).filter(models.StoryRecord.story_id == req.story_id), models.StoryRecord, user_id).first()
    if not story:
        return {"success": False, "message": "story not found"}
    story.title = req.title.strip()
    db.commit()
    return {"success": True, "story_id": story.story_id, "title": story.title}


@router.post("/story/branches/rename")
def rename_branch(req: BranchRenameRequest, db: Session = Depends(get_db), current_user: Optional[AuthUser] = Depends(get_current_user_sync)):
    user_id = current_user_id(current_user)
    return _rename_branch_display_name(db, req.session_id, req.display_name, user_id)


@router.post("/story/saves/create")
def create_new_save(db: Session = Depends(get_db), current_user: Optional[AuthUser] = Depends(get_current_user_sync)):
    return create_new_story(db=db, current_user=current_user)


@router.post("/story/stories/create")
def create_new_story(db: Session = Depends(get_db), current_user: Optional[AuthUser] = Depends(get_current_user_sync)):
    user_id = current_user_id(current_user)
    session = models.SessionState(session_id=build_unique_session_id(user_id=user_id), total_word_count=0, user_id=user_id)
    db.add(session)
    db.commit()
    _, story, branch, _ = ensure_story_branch(db, session.session_id, user_id)
    _set_branch_display_name(branch, "main")
    db.commit()
    return {"success": True, "session_id": session.session_id, "story_id": story.story_id, "branch_id": branch.branch_id}


@router.post("/story/branches/create")
def create_branch(req: CreateBranchRequest, db: Session = Depends(get_db), current_user: Optional[AuthUser] = Depends(get_current_user_sync)):
    user_id = current_user_id(current_user)
    source_session = owner_only(db.query(models.SessionState).filter(models.SessionState.session_id == req.source_session_id), models.SessionState, user_id).first()
    if not source_session:
        return {"success": False, "message": "source save not found"}

    _, story, source_branch, _ = ensure_story_branch(db, req.source_session_id, user_id)
    source_segments = owner_only(db.query(models.StorySegment).filter(models.StorySegment.session_id == req.source_session_id), models.StorySegment, user_id).order_by(models.StorySegment.order_index).all()
    existing_branches = owner_only(db.query(models.SessionBranch).filter(models.SessionBranch.story_id == story.story_id), models.SessionBranch, user_id).all()
    new_session_id = build_unique_session_id(user_id=user_id)
    new_session = models.SessionState(
        session_id=new_session_id,
        user_id=user_id,
        current_script_id=source_session.current_script_id,
        current_dungeon_id=source_session.current_dungeon_id,
        current_node_id=source_session.current_node_id,
        player_position_json=source_session.player_position_json,
        global_state_json=source_session.global_state_json,
        total_word_count=source_session.total_word_count or 0,
    )
    db.add(new_session)
    db.flush()

    segment_pairs = _copy_story_segments(db, source_segments, new_session_id, user_id)
    copy_segment_logs(db, req.source_session_id, new_session_id, segment_pairs, user_id)
    _copy_memory_records(db, story.story_id, req.source_session_id, new_session_id, segment_pairs, user_id)
    _copy_session_characters(db, req.source_session_id, new_session_id, user_id)

    new_branch = models.SessionBranch(
        branch_id=f"branch_{uuid.uuid4().hex[:12]}",
        story_id=story.story_id,
        session_id=new_session_id,
        user_id=user_id,
        parent_branch_id=source_branch.branch_id,
        source_segment_id=source_segments[-1].segment_id if source_segments else None,
        branch_type="branch",
        status="active",
        active_preset_id=source_branch.active_preset_id,
        active_llm_config_id=source_branch.active_llm_config_id,
        active_model=source_branch.active_model,
        reasoning_strength=source_branch.reasoning_strength,
        summary_short=source_branch.summary_short,
        summary_mid=source_branch.summary_mid,
        last_segment_id=segment_pairs.get(source_segments[-1].segment_id) if source_segments else None,
        meta_json=json.dumps({"display_name": _next_branch_name(existing_branches)}, ensure_ascii=False),
    )
    db.add(new_branch)
    db.commit()
    return {
        "success": True,
        "session_id": new_session_id,
        "story_id": story.story_id,
        "branch_id": new_branch.branch_id,
        "display_name": branch_display_name(new_branch, new_session),
    }


@router.post("/story/saves/delete")
def delete_save(session_id: str = Query(..., description="session id"), db: Session = Depends(get_db), current_user: Optional[AuthUser] = Depends(get_current_user_sync)):
    user_id = current_user_id(current_user)
    session = owner_only(db.query(models.SessionState).filter(models.SessionState.session_id == session_id), models.SessionState, user_id).first()
    if not session:
        return {"success": False, "message": "save not found"}
    owner_only(db.query(models.StorySegment).filter(models.StorySegment.session_id == session_id), models.StorySegment, user_id).delete()
    owner_only(db.query(models.EventLedger).filter(models.EventLedger.session_id == session_id), models.EventLedger, user_id).delete()
    owner_only(db.query(models.VariableStateSnapshot).filter(models.VariableStateSnapshot.session_id == session_id), models.VariableStateSnapshot, user_id).delete()
    owner_only(db.query(models.AgentRunLog).filter(models.AgentRunLog.session_id == session_id), models.AgentRunLog, user_id).delete()
    owner_only(db.query(models.Character).filter(models.Character.session_id == session_id), models.Character, user_id).delete()
    owner_only(db.query(models.CharacterTemplate).filter(models.CharacterTemplate.session_id == session_id), models.CharacterTemplate, user_id).delete()
    delete_logs_for_session(db, session_id, user_id)
    cleanup_branch_story(db, session_id, user_id)
    db.delete(session)
    db.commit()
    return {"success": True}


@router.post("/story/segments/delete_cascade")
def delete_segment_cascade(req: DeleteSegmentCascadeRequest, db: Session = Depends(get_db), current_user: Optional[AuthUser] = Depends(get_current_user_sync)):
    user_id = current_user_id(current_user)
    session = owner_only(db.query(models.SessionState).filter(models.SessionState.session_id == req.session_id), models.SessionState, user_id).first()
    if not session:
        return {"success": False, "message": "save not found"}
    segments_to_delete = owner_only(db.query(models.StorySegment).filter(models.StorySegment.session_id == req.session_id, models.StorySegment.order_index >= req.from_order_index), models.StorySegment, user_id).all()
    delete_logs_for_segments(db, [item.segment_id for item in segments_to_delete], user_id)
    deleted_count = owner_only(db.query(models.StorySegment).filter(models.StorySegment.session_id == req.session_id, models.StorySegment.order_index >= req.from_order_index), models.StorySegment, user_id).delete()
    remaining_segments = owner_only(db.query(models.StorySegment).filter(models.StorySegment.session_id == req.session_id), models.StorySegment, user_id).order_by(models.StorySegment.order_index).all()
    session.total_word_count = sum(seg.paragraph_word_count or 0 for seg in remaining_segments)
    db.commit()
    return {"success": True, "deleted_count": deleted_count, "remaining_count": len(remaining_segments)}


@router.post("/story/saves/copy_from_segment")
def copy_save_from_segment(req: CopySaveFromSegmentRequest, db: Session = Depends(get_db), current_user: Optional[AuthUser] = Depends(get_current_user_sync)):
    user_id = current_user_id(current_user)
    source_session = owner_only(db.query(models.SessionState).filter(models.SessionState.session_id == req.source_session_id), models.SessionState, user_id).first()
    if not source_session:
        return {"success": False, "message": "source save not found"}
    source_segments = owner_only(db.query(models.StorySegment).filter(models.StorySegment.session_id == req.source_session_id, models.StorySegment.order_index <= req.to_order_index), models.StorySegment, user_id).order_by(models.StorySegment.order_index).all()
    if not source_segments:
        return {"success": False, "message": "no segments to copy"}
    new_session = models.SessionState(session_id=build_unique_session_id(user_id=user_id), total_word_count=sum(seg.paragraph_word_count or 0 for seg in source_segments), user_id=user_id, global_state_json=_copy_global_state(source_session, req.source_session_id))
    db.add(new_session)
    db.flush()
    segment_pairs = _copy_story_segments(db, source_segments, new_session.session_id, user_id)
    db.commit()
    copy_segment_logs(db, req.source_session_id, new_session.session_id, segment_pairs, user_id)
    create_branch_from_session_copy(db, new_session.session_id, req.source_session_id, source_segments[-1].segment_id, user_id)
    new_branch = owner_only(db.query(models.SessionBranch).filter(models.SessionBranch.session_id == new_session.session_id), models.SessionBranch, user_id).first()
    if new_branch:
        _set_branch_display_name(new_branch, _next_branch_name(owner_only(db.query(models.SessionBranch).filter(models.SessionBranch.story_id == new_branch.story_id), models.SessionBranch, user_id).all()))
        db.commit()
    return {"success": True, "new_session_id": new_session.session_id, "copied_segments": len(source_segments)}


def _rename_branch_display_name(db: Session, session_id: str, display_name: str, user_id: Optional[str]):
    session = owner_only(db.query(models.SessionState).filter(models.SessionState.session_id == session_id), models.SessionState, user_id).first()
    if not session:
        return {"success": False, "message": "save not found"}
    _, _, branch, _ = ensure_story_branch(db, session_id, user_id)
    _set_branch_display_name(branch, display_name.strip())
    db.commit()
    return {"success": True, "session_id": session_id, "display_name": branch_display_name(branch, session)}


def _set_branch_display_name(branch: models.SessionBranch, display_name: str) -> None:
    meta = load_json(branch.meta_json, {})
    meta["display_name"] = display_name
    branch.meta_json = json.dumps(meta, ensure_ascii=False)


def _next_branch_name(branches: list[models.SessionBranch]) -> str:
    used_names = set()
    branch_count = 0
    for branch in branches:
        meta = load_json(branch.meta_json, {})
        name = str(meta.get("display_name") or "").strip()
        if name:
            used_names.add(name)
        if branch.branch_type != "main":
            branch_count += 1
    candidate_index = max(1, branch_count)
    while True:
        candidate = f"分支 {candidate_index}"
        if candidate not in used_names:
            return candidate
        candidate_index += 1


def _copy_story_segments(db: Session, source_segments: list[models.StorySegment], new_session_id: str, user_id: Optional[str]) -> Dict[str, str]:
    segment_pairs: Dict[str, str] = {}
    for seg in source_segments:
        new_segment_id = f"{new_session_id}_{seg.order_index}_{uuid.uuid4().hex[:8]}"
        segment_pairs[seg.segment_id] = new_segment_id
        db.add(models.StorySegment(segment_id=new_segment_id, session_id=new_session_id, order_index=seg.order_index, user_input=seg.user_input, text=seg.text, dungeon_id=seg.dungeon_id, dungeon_node_id=seg.dungeon_node_id, paragraph_word_count=seg.paragraph_word_count, cumulative_word_count=seg.cumulative_word_count, frontend_duration=seg.frontend_duration, backend_duration=seg.backend_duration, content_thinking=seg.content_thinking, content_story=seg.content_story, content_summary=seg.content_summary, content_actions=seg.content_actions, user_id=user_id))
    db.flush()
    return segment_pairs


def _copy_memory_records(db: Session, story_id: str, source_session_id: str, target_session_id: str, segment_pairs: Dict[str, str], user_id: Optional[str]) -> None:
    event_rows = owner_only(db.query(models.EventLedger).filter(models.EventLedger.session_id == source_session_id), models.EventLedger, user_id).all()
    for row in event_rows:
        db.add(models.EventLedger(event_id=f"event_{uuid.uuid4().hex[:12]}", story_id=story_id, session_id=target_session_id, segment_id=segment_pairs.get(row.segment_id), event_type=row.event_type, scope=row.scope, title=row.title, payload_json=row.payload_json, user_id=user_id, created_at=row.created_at))
    snapshot_rows = owner_only(db.query(models.VariableStateSnapshot).filter(models.VariableStateSnapshot.session_id == source_session_id), models.VariableStateSnapshot, user_id).all()
    for row in snapshot_rows:
        db.add(models.VariableStateSnapshot(snapshot_id=f"snapshot_{uuid.uuid4().hex[:12]}", story_id=story_id, session_id=target_session_id, segment_id=segment_pairs.get(row.segment_id), namespace=row.namespace, key=row.key, value_json=row.value_json, user_id=user_id, created_at=row.created_at))
    db.flush()


def _copy_session_characters(db: Session, source_session_id: str, target_session_id: str, user_id: Optional[str]) -> None:
    template_rows = owner_only(db.query(models.CharacterTemplate).filter(models.CharacterTemplate.session_id == source_session_id), models.CharacterTemplate, user_id).all()
    for row in template_rows:
        db.add(models.CharacterTemplate(user_id=user_id, session_id=target_session_id, template_id=row.template_id, template_name=row.template_name, template_json=row.template_json, is_active=row.is_active, created_at=row.created_at, updated_at=row.updated_at))
    character_rows = owner_only(db.query(models.Character).filter(models.Character.session_id == source_session_id), models.Character, user_id).all()
    for row in character_rows:
        db.add(models.Character(user_id=user_id, session_id=target_session_id, template_id=row.template_id, character_id=row.character_id, data_json=row.data_json, created_at=row.created_at, updated_at=row.updated_at))
    db.flush()


def _copy_global_state(source_session: models.SessionState, source_session_id: str) -> str:
    try:
        state = json.loads(source_session.global_state_json) if source_session.global_state_json else {}
        state.pop("display_name", None)
        return json.dumps(state, ensure_ascii=False)
    except Exception:
        return json.dumps({"source_session_id": source_session_id}, ensure_ascii=False)
