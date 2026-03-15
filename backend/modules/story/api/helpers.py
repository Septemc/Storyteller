from __future__ import annotations

import json
import re
from typing import Dict, List, Optional

from ....db import models
from ...characters.services.store import player_profile_from_row
from ...characters.services.profile_utils import extract_basic_summary
from .schemas import BranchInfo, SaveDetail, SaveInfo, SessionSummaryCharacter


def parse_character_basic(ch: models.Character) -> Dict:
    profile = player_profile_from_row(ch)
    basic = profile.get("tab_basic")
    return basic if isinstance(basic, dict) else {}


def load_json(value: Optional[str], default):
    try:
        return json.loads(value) if value else default
    except Exception:
        return default


def first_non_empty(data: Dict, keys: List[str]) -> Optional[str]:
    for key in keys:
        value = data.get(key)
        if value is not None and str(value).strip():
            return str(value).strip()
    return None


def to_character_summary(ch: models.Character) -> SessionSummaryCharacter:
    summary = extract_basic_summary(player_profile_from_row(ch))
    return SessionSummaryCharacter(
        character_id=ch.character_id,
        name=summary.get("name"),
        ability_tier=summary.get("ability_tier"),
    )


def save_display_name(session: models.SessionState) -> str:
    state = load_json(session.global_state_json, {})
    return state.get("display_name") or session.session_id


def branch_display_name(branch: Optional[models.SessionBranch], session: Optional[models.SessionState] = None) -> str:
    if not branch:
        return save_display_name(session) if session else "未命名分支"
    meta = load_json(branch.meta_json, {})
    if meta.get("display_name"):
        return str(meta["display_name"]).strip()
    if branch.branch_type == "main":
        return "main"
    if session:
        session_name = save_display_name(session)
        if session_name and session_name != session.session_id:
            return session_name
        return session.session_id
    return branch.branch_id


def build_segment_preview(segment: models.StorySegment) -> str:
    if segment.content_summary:
        return segment.content_summary[:80] + ("..." if len(segment.content_summary) > 80 else "")
    if segment.user_input:
        return segment.user_input[:80] + ("..." if len(segment.user_input) > 80 else "")
    first_sentence = re.split(r"[。！？\n]", segment.text or "")
    text = first_sentence[0].strip() if first_sentence and first_sentence[0].strip() else (segment.text or "")
    return text[:80] + ("..." if len(text) > 80 else "")


def save_info_from_session(session: models.SessionState, segment_count: int) -> SaveInfo:
    return SaveInfo(session_id=session.session_id, display_name=save_display_name(session), segment_count=segment_count, total_word_count=session.total_word_count or 0, created_at=session.updated_at.isoformat() if session.updated_at else None, updated_at=session.updated_at.isoformat() if session.updated_at else None)


def save_info_with_branch(session: models.SessionState, branch: Optional[models.SessionBranch], story: Optional[models.StoryRecord], segment_count: int) -> SaveInfo:
    info = save_info_from_session(session, segment_count)
    info.story_id = getattr(story, "story_id", None)
    info.story_title = getattr(story, "title", None)
    info.branch_id = getattr(branch, "branch_id", None)
    info.branch_display_name = branch_display_name(branch, session)
    info.branch_type = getattr(branch, "branch_type", None)
    info.branch_status = getattr(branch, "status", None)
    info.parent_branch_id = getattr(branch, "parent_branch_id", None)
    info.reasoning_strength = getattr(branch, "reasoning_strength", None)
    return info


def build_branch_info(branch: models.SessionBranch, session: Optional[models.SessionState], segment_count: int = 0, total_word_count: int = 0) -> BranchInfo:
    return BranchInfo(
        branch_id=branch.branch_id,
        session_id=branch.session_id,
        display_name=branch_display_name(branch, session),
        branch_type=branch.branch_type,
        status=branch.status,
        parent_branch_id=branch.parent_branch_id,
        last_segment_id=branch.last_segment_id,
        reasoning_strength=branch.reasoning_strength,
        segment_count=segment_count,
        total_word_count=total_word_count,
        created_at=branch.created_at.isoformat() if branch.created_at else None,
        updated_at=branch.updated_at.isoformat() if branch.updated_at else None,
    )


def empty_save_detail(session_id: str) -> SaveDetail:
    return SaveDetail(session_id=session_id, display_name="未知存档", segment_count=0, total_word_count=0, segments=[], branches=[])
