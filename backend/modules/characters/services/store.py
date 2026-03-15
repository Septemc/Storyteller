from __future__ import annotations

from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from ....core.tenant import owner_only, owner_or_public
from ....db import models
from .profile_utils import (
    apply_status_to_name,
    build_player_profile,
    default_character_data,
    dump_json,
    extract_basic_summary,
    extract_name,
    full_profile_from_data,
    load_json,
    meta_from_data,
    normalize_full_profile,
    parse_data_json,
    player_profile_from_data,
    unwrap_template_config,
)


def owner_character_query(db: Session, owner_id: Optional[str], session_id: str):
    return owner_only(
        db.query(models.Character).filter(models.Character.session_id == session_id),
        models.Character,
        owner_id,
    )


def resolve_template_payload(db: Session, session_id: str, template_id: Optional[str], owner_id: Optional[str]) -> Optional[Dict[str, Any]]:
    if not template_id:
        return None
    row = owner_or_public(
        db.query(models.CharacterTemplate).filter(models.CharacterTemplate.session_id == session_id, models.CharacterTemplate.template_id == template_id),
        models.CharacterTemplate,
        owner_id,
    ).first()
    if not row:
        return None
    return {
        "id": row.template_id,
        "template_id": row.template_id,
        "session_id": row.session_id,
        "name": row.template_name,
        "is_active": row.is_active,
        "config": unwrap_template_config(load_json(row.template_json, {})),
    }


def character_payload(row: models.Character, db: Session, owner_id: Optional[str]) -> Dict[str, Any]:
    template = resolve_template_payload(db, row.session_id, row.template_id, owner_id)
    data = data_payload_from_row(row)
    full_profile = full_profile_from_row(row)
    player_profile = player_profile_from_row(row, template)
    meta = meta_from_row(row)
    return {
        "user_id": row.user_id,
        "session_id": row.session_id,
        "character_id": row.character_id,
        "template_id": row.template_id,
        "display_name": meta.get("player_name") or extract_name(player_profile),
        "developer_name": meta.get("developer_name") or extract_name(full_profile),
        "status": meta.get("status") or "active",
        "source_type": meta.get("source_type") or "manual",
        "template": template,
        "data_json": data,
        "full_profile": full_profile,
        "player_profile": player_profile,
        "meta": meta,
        "type": full_profile.get("type") or "npc",
    }


def data_payload_from_row(row: models.Character) -> Dict[str, Any]:
    return parse_data_json(row.data_json)


def full_profile_from_row(row: models.Character) -> Dict[str, Any]:
    return full_profile_from_data(data_payload_from_row(row), row.character_id, row.template_id)


def player_profile_from_row(row: models.Character, template: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    return player_profile_from_data(data_payload_from_row(row), row.character_id, row.template_id, template)


def meta_from_row(row: models.Character) -> Dict[str, Any]:
    return meta_from_data(data_payload_from_row(row))


def list_character_items(db: Session, owner_id: Optional[str], session_id: str, q: str = "") -> List[Dict[str, Any]]:
    keyword = str(q or "").strip().lower()
    items: List[Dict[str, Any]] = []
    for row in owner_character_query(db, owner_id, session_id).order_by(models.Character.updated_at.desc()).all():
        item = character_payload(row, db, owner_id)
        search_blob = " ".join([item["character_id"], item["display_name"], item["developer_name"], item["status"]]).lower()
        if keyword and keyword not in search_blob:
            continue
        summary = extract_basic_summary(item["player_profile"])
        items.append(
            {
                "session_id": item["session_id"],
                "character_id": item["character_id"],
                "display_name": item["display_name"],
                "developer_name": item["developer_name"],
                "type": item["type"],
                "status": item["status"],
                "source_type": item["source_type"],
                "template_id": item["template_id"],
                "ability_tier": summary.get("ability_tier"),
            }
        )
    return items


def get_character_row(db: Session, owner_id: Optional[str], session_id: str, character_id: str) -> Optional[models.Character]:
    return owner_character_query(db, owner_id, session_id).filter(models.Character.character_id == character_id).first()


def upsert_character(db: Session, owner_id: Optional[str], payload: Dict[str, Any]) -> models.Character:
    session_id = str(payload.get("session_id") or "").strip()
    character_id = str(payload.get("character_id") or "").strip()
    if not session_id:
        raise ValueError("session_id is required")
    if not character_id:
        raise ValueError("character_id is required")
    row = get_character_row(db, owner_id, session_id, character_id)
    if not row:
        row = models.Character(session_id=session_id, character_id=character_id, user_id=owner_id)
        db.add(row)
    template_id = payload.get("template_id") or row.template_id or ""
    template = resolve_template_payload(db, session_id, template_id, owner_id)
    full_profile = normalize_full_profile(payload.get("full_profile") or {}, character_id, template_id)
    player_profile = normalize_full_profile(payload.get("player_profile") or build_player_profile(full_profile, template), character_id, template_id)
    meta = dict(payload.get("meta") or {})
    status = payload.get("status") or meta.get("status") or "active"
    source_type = payload.get("source_type") or meta.get("source_type") or "manual"
    _apply_status_suffix(full_profile, status)
    _apply_status_suffix(player_profile, status)
    meta["status"] = status
    meta["source_type"] = source_type
    meta["developer_name"] = apply_status_to_name(extract_name(full_profile), status)
    meta["player_name"] = apply_status_to_name(extract_name(player_profile), status)
    if template:
        meta["template_snapshot"] = template
    row.template_id = template_id
    row.data_json = dump_json(default_character_data(full_profile, player_profile, meta))
    return row


def export_character_rows(db: Session, owner_id: Optional[str], session_id: str) -> List[Dict[str, Any]]:
    return [character_payload(row, db, owner_id) for row in owner_character_query(db, owner_id, session_id).all()]


def _apply_status_suffix(profile: Dict[str, Any], status: str) -> None:
    basic = profile.get("tab_basic")
    if not isinstance(basic, dict):
        return
    for key in ["f_name", "name", "f_nickname", "nickname"]:
        if basic.get(key):
            basic[key] = apply_status_to_name(str(basic.get(key) or ""), status)
            break
