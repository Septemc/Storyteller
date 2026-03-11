import json
import time
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Body, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import or_
from sqlalchemy.orm import Session

from ..core.auth import User as AuthUser, get_current_user
from ..core.tenant import current_user_id, owner_only, owner_or_public, resolve_scoped_id
from ..db import models
from ..db.base import get_db

router = APIRouter()

TAB_FIELD_MAPPING = {
    "tab_basic": ("basic_json", {}),
    "tab_knowledge": ("knowledge_json", {}),
    "tab_secrets": ("secrets_json", {}),
    "tab_attributes": ("attributes_json", {}),
    "tab_relations": ("relations_json", {}),
    "tab_equipment": ("equipment_json", []),
    "tab_items": ("items_json", []),
    "tab_skills": ("skills_json", []),
    "tab_fortune": ("fortune_json", {}),
}


class CharacterListItem(BaseModel):
    character_id: str
    type: str
    basic: Dict[str, Any] = Field(default_factory=dict)


class CharacterListResponse(BaseModel):
    items: List[CharacterListItem] = Field(default_factory=list)


def _load_json(value: Optional[str], default: Any) -> Any:
    if not value:
        return default
    try:
        return json.loads(value)
    except Exception:
        return default


def _generate_character_id() -> str:
    return f"NPC_{int(time.time() * 1000)}"


def _extract_categorized_data(item: Dict[str, Any]) -> Dict[str, str]:
    result: Dict[str, str] = {}
    aliases = {
        "basic_json": ["tab_basic", "basic"],
        "knowledge_json": ["tab_knowledge", "knowledge"],
        "secrets_json": ["tab_secrets", "secrets"],
        "attributes_json": ["tab_attributes", "attributes"],
        "relations_json": ["tab_relations", "relations"],
        "equipment_json": ["tab_equipment", "equipment"],
        "items_json": ["tab_items", "items"],
        "skills_json": ["tab_skills", "skills"],
        "fortune_json": ["tab_fortune", "fortune"],
    }
    for db_field, source_keys in aliases.items():
        data = None
        for key in source_keys:
            if key in item:
                data = item[key]
                break
        if data is None:
            data = [] if db_field in {"equipment_json", "items_json", "skills_json"} else {}
        result[db_field] = json.dumps(data, ensure_ascii=False)
    return result


def _owner_character_query(db: Session, owner_id: Optional[str]):
    return owner_only(db.query(models.Character), models.Character, owner_id)


def _list_character_query(db: Session, owner_id: Optional[str]):
    return owner_or_public(db.query(models.Character), models.Character, owner_id)


def _build_character_detail(ch: models.Character) -> Dict[str, Any]:
    full_data = _load_json(ch.data_json, {})
    if not isinstance(full_data, dict):
        full_data = {}

    for tab_name, (db_field, default_value) in TAB_FIELD_MAPPING.items():
        value = getattr(ch, db_field)
        if value:
            full_data[tab_name] = _load_json(value, default_value)
        else:
            full_data.setdefault(tab_name, default_value)

    full_data["character_id"] = ch.character_id
    full_data["type"] = ch.type
    full_data["template_id"] = ch.template_id or "system_default"
    return full_data


def _resolve_character_id(
    db: Session,
    preferred_id: str,
    owner_id: Optional[str],
) -> str:
    return resolve_scoped_id(db, models.Character, "character_id", preferred_id, owner_id)


@router.post("/characters/import")
def import_characters(
    payload: Any = Body(...),
    db: Session = Depends(get_db),
    current_user: Optional[AuthUser] = Depends(get_current_user),
):
    owner_id = current_user_id(current_user)
    items = payload if isinstance(payload, list) else [payload]
    imported_count = 0

    for item in items:
        if not isinstance(item, dict):
            continue

        preferred_id = item.get("character_id") or _generate_character_id()
        character_id = _resolve_character_id(db, preferred_id, owner_id)

        raw_data = dict(item)
        raw_data["character_id"] = character_id
        raw_data.setdefault("type", "npc")
        raw_data.setdefault("template_id", "system_default")
        categorized = _extract_categorized_data(raw_data)

        existing = _owner_character_query(db, owner_id).filter(models.Character.character_id == character_id).first()
        if existing:
            row = existing
        else:
            row = models.Character(character_id=character_id, user_id=owner_id)
            db.add(row)

        row.type = raw_data.get("type", row.type or "npc")
        row.template_id = raw_data.get("template_id", row.template_id or "system_default")
        row.data_json = json.dumps(raw_data, ensure_ascii=False)
        for field, value in categorized.items():
            setattr(row, field, value)
        imported_count += 1

    db.commit()
    return {"message": f"成功导入 {imported_count} 个角色。", "count": imported_count}


@router.get("/characters/export/all")
def export_all_characters(
    db: Session = Depends(get_db),
    current_user: Optional[AuthUser] = Depends(get_current_user),
):
    owner_id = current_user_id(current_user)
    rows = _owner_character_query(db, owner_id).all()
    return [_build_character_detail(ch) for ch in rows]


@router.get("/characters/{character_id}")
def get_character(
    character_id: str,
    db: Session = Depends(get_db),
    current_user: Optional[AuthUser] = Depends(get_current_user),
):
    owner_id = current_user_id(current_user)
    ch = _owner_character_query(db, owner_id).filter(models.Character.character_id == character_id).first()
    if not ch:
        raise HTTPException(status_code=404, detail="角色不存在")
    return _build_character_detail(ch)


@router.get("/characters", response_model=CharacterListResponse)
def list_characters(
    q: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: Optional[AuthUser] = Depends(get_current_user),
):
    owner_id = current_user_id(current_user)
    query = _list_character_query(db, owner_id)
    if q:
        like = f"%{q}%"
        query = query.filter(
            or_(
                models.Character.character_id.like(like),
                models.Character.basic_json.like(like),
                models.Character.data_json.like(like),
            )
        )
    rows = query.order_by(models.Character.updated_at.desc()).all()

    items = []
    for row in rows:
        basic = _load_json(row.basic_json, {})
        if not isinstance(basic, dict):
            basic = {}
        items.append(
            CharacterListItem(
                character_id=row.character_id,
                type=row.type,
                basic=basic,
            )
        )
    return CharacterListResponse(items=items)


@router.delete("/characters/clear_all")
def clear_all_characters(
    db: Session = Depends(get_db),
    current_user: Optional[AuthUser] = Depends(get_current_user),
):
    owner_id = current_user_id(current_user)
    try:
        deleted = _owner_character_query(db, owner_id).delete(synchronize_session=False)
        db.commit()
        return {"message": f"成功清空角色库，共删除 {deleted} 个角色。", "count": deleted}
    except Exception as exc:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"清空失败: {exc}") from exc


@router.put("/characters/{character_id}")
def update_character(
    character_id: str,
    payload: Any = Body(...),
    db: Session = Depends(get_db),
    current_user: Optional[AuthUser] = Depends(get_current_user),
):
    owner_id = current_user_id(current_user)
    ch = _owner_character_query(db, owner_id).filter(models.Character.character_id == character_id).first()
    if not ch:
        raise HTTPException(status_code=404, detail="角色不存在")
    if not isinstance(payload, dict):
        raise HTTPException(status_code=400, detail="角色数据必须是 JSON 对象")

    raw_data = dict(payload)
    raw_data["character_id"] = character_id
    raw_data.setdefault("type", ch.type or "npc")
    raw_data.setdefault("template_id", ch.template_id or "system_default")
    categorized = _extract_categorized_data(raw_data)

    ch.type = raw_data.get("type", ch.type)
    ch.template_id = raw_data.get("template_id", ch.template_id)
    ch.data_json = json.dumps(raw_data, ensure_ascii=False)
    for field, value in categorized.items():
        setattr(ch, field, value)

    db.commit()
    db.refresh(ch)
    return _build_character_detail(ch)


@router.delete("/characters/{character_id}")
def delete_character(
    character_id: str,
    db: Session = Depends(get_db),
    current_user: Optional[AuthUser] = Depends(get_current_user),
):
    owner_id = current_user_id(current_user)
    ch = _owner_character_query(db, owner_id).filter(models.Character.character_id == character_id).first()
    if not ch:
        raise HTTPException(status_code=404, detail="角色不存在")
    db.delete(ch)
    db.commit()
    return {"status": "ok"}
