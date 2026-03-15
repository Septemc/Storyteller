from __future__ import annotations

import json
import re
import uuid
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from ....core.llm_client import chat_completion
from ....core.tenant import owner_only
from ....db import models
from ...story.services.content_parser import extract_story_parts
from .store import character_payload, resolve_template_payload, upsert_character


def sync_characters_after_turn(
    db: Session,
    state: Dict[str, Any],
    segment_id: str,
    story_text: str,
    user_id: Optional[str],
) -> Dict[str, Any]:
    session_id = state["session_id"]
    template = _pick_template(db, state, user_id)
    rows = owner_only(
        db.query(models.Character).filter(models.Character.session_id == session_id),
        models.Character,
        user_id,
    ).all()
    existing = [character_payload(row, db, user_id) for row in rows]
    if not template:
        return {"created": [], "updated": [], "skipped": "no_template"}
    result = _model_sync(state, template, existing, story_text)
    for item in result.get("created", []):
        item.setdefault("character_id", f"C_{uuid.uuid4().hex[:10]}")
        upsert_character(
            db,
            user_id,
            {
                "session_id": session_id,
                "character_id": item["character_id"],
                "template_id": template["id"],
                "status": item.get("status") or "active",
                "source_type": "dynamic",
                "full_profile": item.get("full_profile") or {},
                "player_profile": item.get("player_profile") or {},
                "meta": {"last_synced_segment_id": segment_id, "sync_reason": item.get("reason", "")},
            },
        )
    existing_by_id = {item["character_id"]: item for item in existing}
    existing_by_name = {item["developer_name"]: item for item in existing if item.get("developer_name")}
    for item in result.get("updated", []):
        base = existing_by_id.get(item.get("character_id")) or existing_by_name.get(item.get("name"))
        if not base:
            continue
        upsert_character(
            db,
            user_id,
            {
                "session_id": session_id,
                "character_id": base["character_id"],
                "template_id": base["template_id"],
                "status": item.get("status") or base["status"],
                "source_type": base["source_type"],
                "full_profile": _deep_merge(base["full_profile"], item.get("full_patch") or {}),
                "player_profile": _deep_merge(base["player_profile"], item.get("player_patch") or {}),
                "meta": {"last_synced_segment_id": segment_id, "sync_reason": item.get("reason", "")},
            },
        )
    db.commit()
    return result


def _pick_template(db: Session, state: Dict[str, Any], user_id: Optional[str]) -> Optional[Dict[str, Any]]:
    session_id = state["session_id"]
    row = owner_only(
        db.query(models.CharacterTemplate).filter(models.CharacterTemplate.session_id == session_id, models.CharacterTemplate.is_active == True),
        models.CharacterTemplate,
        user_id,
    ).first()
    if row:
        return resolve_template_payload(db, session_id, row.template_id, user_id)
    main_character = state.get("context", {}).get("main_character") or {}
    template_id = main_character.get("template_id") or state.get("runtime", {}).get("character_template_id")
    if template_id:
        return resolve_template_payload(db, session_id, template_id, user_id)
    row = owner_only(
        db.query(models.CharacterTemplate).filter(models.CharacterTemplate.session_id == session_id),
        models.CharacterTemplate,
        user_id,
    ).first()
    return resolve_template_payload(db, session_id, row.template_id, user_id) if row else None


def _model_sync(state: Dict[str, Any], template: Dict[str, Any], existing: List[Dict[str, Any]], story_text: str) -> Dict[str, Any]:
    llm_cfg = state.get("runtime", {}).get("llm_cfg") or {}
    model = state.get("runtime", {}).get("model")
    story_body = extract_story_parts(story_text).get("story") or story_text
    if not llm_cfg or not model or not story_body.strip():
        return {"created": [], "updated": [], "skipped": "no_model"}
    try:
        content, _ = chat_completion(
            base_url=str(llm_cfg.get("base_url") or ""),
            api_key=str(llm_cfg.get("api_key") or ""),
            model=str(model),
            messages=_build_messages(template, existing, story_body),
            temperature=0.2,
            stream=False,
            timeout_s=60,
        )
        return _parse_result(content)
    except Exception as exc:
        return {"created": [], "updated": [], "skipped": f"error:{type(exc).__name__}:{exc}"}


def _build_messages(template: Dict[str, Any], existing: List[Dict[str, Any]], story_body: str) -> List[Dict[str, str]]:
    fields = template.get("config", {}).get("fields") or []
    field_lines = [f"- {field.get('path')}: {field.get('desc') or field.get('label') or field.get('id')}" for field in fields[:40]]
    existing_lines = [f"- {item['character_id']} | {item.get('developer_name') or item.get('display_name')} | {item.get('status')}" for item in existing[:40]]
    prompt = "\n".join(
        [
            "You are a character synchronization skill for an interactive fiction system.",
            "This skill is always called after the final story body is generated.",
            "Read only the latest story body and update the current session character set.",
            "Return JSON only.",
            'Schema: {"created":[{"character_id":"","status":"active","reason":"","full_profile":{},"player_profile":{}}],"updated":[{"character_id":"","name":"","status":"active","reason":"","full_patch":{},"player_patch":{}}]}',
            "Rules:",
            "- If no character information changed, return empty arrays.",
            "- If a new person appears in the latest story body, create a new character card.",
            "- If an existing character changes state, relation, known information, inventory or identity, update it.",
            "- Hidden information belongs only in full_profile. player_profile must contain only what the player can know now.",
            "- If a character dies or exits, set status to 死亡, 退场 or 失踪 and keep the card instead of deleting it.",
            "[Template Fields]",
            *field_lines,
            "[Existing Session Characters]",
            *existing_lines,
            "[Latest Story Body]",
            story_body,
        ]
    )
    return [{"role": "system", "content": prompt}]


def _parse_result(content: str) -> Dict[str, Any]:
    text = str(content or "").strip()
    match = re.search(r"\{[\s\S]*\}", text)
    if not match:
        return {"created": [], "updated": [], "skipped": "invalid_json"}
    try:
        payload = json.loads(match.group(0))
        return {"created": payload.get("created") or [], "updated": payload.get("updated") or []}
    except json.JSONDecodeError:
        return {"created": [], "updated": [], "skipped": "invalid_json"}


def _deep_merge(base: Any, patch: Any) -> Any:
    if isinstance(base, dict) and isinstance(patch, dict):
        merged = dict(base)
        for key, value in patch.items():
            merged[key] = _deep_merge(merged.get(key), value)
        return merged
    return patch if patch not in (None, "") else base
