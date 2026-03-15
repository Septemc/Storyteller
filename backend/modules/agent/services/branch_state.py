from __future__ import annotations

import json
import uuid
from typing import Any, Dict, Optional, Tuple

from sqlalchemy.orm import Session

from ....core import storage
from ....core.session_state import ensure_session_state
from ....core.tenant import owner_only
from ....db import models
from ....modules.story.api.helpers import load_json


def ensure_story_branch(db: Session, session_id: str, user_id: Optional[str]) -> Tuple[models.SessionState, models.StoryRecord, models.SessionBranch, Dict[str, Any]]:
    session_state = ensure_session_state(db, session_id, user_id=user_id)
    global_state = load_json(session_state.global_state_json, {})
    branch = owner_only(db.query(models.SessionBranch).filter(models.SessionBranch.session_id == session_id), models.SessionBranch, user_id).first()
    if branch:
        story = owner_only(db.query(models.StoryRecord).filter(models.StoryRecord.story_id == branch.story_id), models.StoryRecord, user_id).first()
        if story:
            return session_state, story, branch, global_state
    title = global_state.get("display_name") or f"Story {session_id[-8:]}"
    story = models.StoryRecord(story_id=f"story_{uuid.uuid4().hex[:12]}", title=title, user_id=user_id, meta_json=json.dumps({"source": "session_bootstrap"}, ensure_ascii=False))
    db.add(story)
    if branch:
        branch.story_id = story.story_id
    else:
        branch = models.SessionBranch(branch_id=f"branch_{uuid.uuid4().hex[:12]}", story_id=story.story_id, session_id=session_id, user_id=user_id, branch_type="main")
        db.add(branch)
    db.commit()
    db.refresh(story)
    db.refresh(branch)
    return session_state, story, branch, global_state


def create_branch_from_session_copy(db: Session, new_session_id: str, source_session_id: str, source_segment_id: Optional[str], user_id: Optional[str]) -> None:
    _, source_story, source_branch, _ = ensure_story_branch(db, source_session_id, user_id)
    branch = models.SessionBranch(
        branch_id=f"branch_{uuid.uuid4().hex[:12]}",
        story_id=source_story.story_id,
        session_id=new_session_id,
        user_id=user_id,
        parent_branch_id=source_branch.branch_id,
        source_segment_id=source_segment_id,
        branch_type="save_copy",
    )
    db.add(branch)
    db.commit()


def cleanup_branch_story(db: Session, session_id: str, user_id: Optional[str]) -> None:
    branch = owner_only(db.query(models.SessionBranch).filter(models.SessionBranch.session_id == session_id), models.SessionBranch, user_id).first()
    if not branch:
        return
    story_id = branch.story_id
    db.delete(branch)
    db.commit()
    remaining = owner_only(db.query(models.SessionBranch).filter(models.SessionBranch.story_id == story_id), models.SessionBranch, user_id).count()
    if remaining:
        return
    story = owner_only(db.query(models.StoryRecord).filter(models.StoryRecord.story_id == story_id), models.StoryRecord, user_id).first()
    if story:
        db.delete(story)
        db.commit()


def resolve_runtime_settings(db: Session, session_state: models.SessionState, branch: models.SessionBranch, global_state: Dict[str, Any], requested_strength: Optional[str], user_id: Optional[str]) -> Dict[str, Any]:
    preset = _preset_by_id(db, branch.active_preset_id or global_state.get("active_preset_id"), user_id) or storage.get_active_preset(db, user_id)
    llm_cfg = _llm_by_id(db, branch.active_llm_config_id or global_state.get("active_llm_config_id"), user_id) or storage.get_active_llm_config(db, user_id=user_id)
    active = storage.get_llm_active(db, user_id=user_id)
    model = branch.active_model or global_state.get("active_model") or active.get("model") or (llm_cfg or {}).get("default_model")
    strength = requested_strength or branch.reasoning_strength or global_state.get("reasoning_strength") or "low"
    return {"preset": preset, "llm_cfg": llm_cfg, "model": model, "reasoning_strength": strength}


def update_branch_runtime(db: Session, branch: models.SessionBranch, runtime: Dict[str, Any]) -> None:
    branch.active_preset_id = (runtime.get("preset") or {}).get("id")
    branch.active_llm_config_id = (runtime.get("llm_cfg") or {}).get("id")
    branch.active_model = runtime.get("model")
    branch.reasoning_strength = runtime.get("reasoning_strength") or branch.reasoning_strength
    db.commit()


def _preset_by_id(db: Session, preset_id: Optional[str], user_id: Optional[str]) -> Optional[Dict[str, Any]]:
    if not preset_id:
        return None
    row = owner_only(db.query(models.DBPreset).filter(models.DBPreset.id == preset_id), models.DBPreset, user_id).first()
    if not row:
        return None
    data = load_json(row.config_json, {})
    return {"id": row.id, "name": row.name, "version": row.version, "root": data.get("root", {}), "meta": data.get("meta", {})}


def _llm_by_id(db: Session, config_id: Optional[str], user_id: Optional[str]) -> Optional[Dict[str, Any]]:
    if not config_id:
        return None
    row = owner_only(db.query(models.DBLLMConfig).filter(models.DBLLMConfig.id == config_id), models.DBLLMConfig, user_id).first()
    if not row:
        return None
    return {"id": row.id, "name": row.name, "base_url": row.base_url, "api_key": row.api_key, "stream": row.stream, "default_model": row.default_model}
