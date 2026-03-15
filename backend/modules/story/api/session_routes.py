from __future__ import annotations

import json
from typing import Dict, Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ....core.auth import User as AuthUser, get_current_user_sync
from ....core.session_state import SessionStateConflictError, ensure_session_state
from ....core.tenant import current_user_id, owner_only
from ....db import models
from ....db.base import get_db
from ....modules.agent.services.branch_state import ensure_story_branch
from ...characters.services.store import player_profile_from_row
from ...characters.services.profile_utils import extract_basic_summary
from .helpers import to_character_summary
from .schemas import SessionContextUpdateRequest, SessionSummaryDungeon, SessionSummaryResponse, SessionSummaryVariables

router = APIRouter()


@router.post("/session/context", response_model=SessionSummaryResponse)
def update_session_context(req: SessionContextUpdateRequest, db: Session = Depends(get_db), current_user: Optional[AuthUser] = Depends(get_current_user_sync)) -> SessionSummaryResponse:
    user_id = current_user_id(current_user)
    try:
        session_state = ensure_session_state(db, req.session_id, user_id=user_id)
    except SessionStateConflictError as exc:
        raise HTTPException(status_code=409, detail="session belongs to another user scope") from exc
    _, _, branch, _ = ensure_story_branch(db, req.session_id, user_id)
    provided_fields = getattr(req, "model_fields_set", set())
    if "current_script_id" in provided_fields:
        session_state.current_script_id = req.current_script_id
    if "current_dungeon_id" in provided_fields:
        session_state.current_dungeon_id = req.current_dungeon_id
    if "current_node_id" in provided_fields:
        session_state.current_node_id = req.current_node_id
    global_state = json.loads(session_state.global_state_json) if session_state.global_state_json else {}
    if not isinstance(global_state, dict):
        global_state = {}
    for key in ["main_character_id", "active_preset_id", "active_llm_config_id", "active_model", "reasoning_strength"]:
        if key in provided_fields:
            value = getattr(req, key)
            if value:
                global_state[key] = value
            else:
                global_state.pop(key, None)
    branch.active_preset_id = global_state.get("active_preset_id")
    branch.active_llm_config_id = global_state.get("active_llm_config_id")
    branch.active_model = global_state.get("active_model")
    branch.reasoning_strength = global_state.get("reasoning_strength") or branch.reasoning_strength
    session_state.global_state_json = json.dumps(global_state, ensure_ascii=False)
    db.commit()
    dungeon = owner_only(db.query(models.Dungeon).filter(models.Dungeon.dungeon_id == session_state.current_dungeon_id), models.Dungeon, user_id).first() if session_state.current_dungeon_id else None
    node = db.query(models.DungeonNode).filter(models.DungeonNode.dungeon_id == session_state.current_dungeon_id, models.DungeonNode.node_id == session_state.current_node_id).first() if session_state.current_node_id else None
    dungeon_block = SessionSummaryDungeon(name=dungeon.name if dungeon else None, current_node_name=node.name if node else None, progress_hint=f"{int(node.progress_percent)}%" if node and node.progress_percent is not None else "unknown") if session_state.current_dungeon_id else None
    characters = [to_character_summary(ch) for ch in owner_only(db.query(models.Character).filter(models.Character.session_id == req.session_id), models.Character, user_id).limit(5).all()]
    variables = SessionSummaryVariables(main_character=_build_main_character_summary(db, req.session_id, global_state.get("main_character_id"), user_id), faction_summary=None)
    return SessionSummaryResponse(dungeon=dungeon_block, characters=characters, variables=variables)


def _build_main_character_summary(db: Session, session_id: str, main_character_id: Optional[str], user_id: Optional[str]) -> Optional[Dict]:
    if not main_character_id:
        return None
    main_char = owner_only(db.query(models.Character).filter(models.Character.session_id == session_id, models.Character.character_id == main_character_id), models.Character, user_id).first()
    if not main_char:
        return None
    summary = extract_basic_summary(player_profile_from_row(main_char))
    return {
        "character_id": main_char.character_id,
        "name": summary.get("name"),
        "ability_tier": summary.get("ability_tier"),
        "economy_summary": summary.get("economy_summary"),
    }
