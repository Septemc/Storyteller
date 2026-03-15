from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Optional

from fastapi import APIRouter, Body, Depends, HTTPException
from sqlalchemy.orm import Session

from ....core import prompts
from ....core.auth import User as AuthUser, get_current_user_sync
from ....core.tenant import current_user_id, owner_only, resolve_scoped_id, scoped_default_id
from ....db.base import get_db
from ....db.models import DBPreset
from .preset_schemas import PresetIn

router = APIRouter()
DEFAULT_PRESET_PATH = Path(__file__).resolve().parents[4] / "data" / "default_preset.json"
DEFAULT_PRESET_ID = "preset_default"


def load_default_preset_from_file() -> Dict[str, Any]:
    return json.loads(DEFAULT_PRESET_PATH.read_text(encoding="utf-8")) if DEFAULT_PRESET_PATH.exists() else prompts.default_preset("默认预设")


def ensure_default_preset_in_db(db: Session, user_id: Optional[str] = None) -> DBPreset:
    default_preset = owner_only(db.query(DBPreset).filter(DBPreset.is_default == True), DBPreset, user_id).first()
    if default_preset:
        return default_preset
    file_preset = load_default_preset_from_file()
    preset_id = scoped_default_id(file_preset.get("id", DEFAULT_PRESET_ID), user_id)
    file_preset["id"] = preset_id
    existing = owner_only(db.query(DBPreset).filter(DBPreset.id == preset_id), DBPreset, user_id).first()
    if existing:
        existing.is_default = True
        db.commit()
        return existing
    db_obj = DBPreset(id=preset_id, name=file_preset.get("name", "默认预设"), version=file_preset.get("version", 1), is_active=True, is_default=True, config_json=json.dumps(file_preset, ensure_ascii=False), user_id=user_id)
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj


@router.get("/presets")
def list_presets(db: Session = Depends(get_db), current_user: Optional[AuthUser] = Depends(get_current_user_sync)):
    user_id = current_user_id(current_user)
    ensure_default_preset_in_db(db, user_id)
    rows = owner_only(db.query(DBPreset), DBPreset, user_id).order_by(DBPreset.is_default.desc(), DBPreset.created_at.asc()).all()
    active_row = owner_only(db.query(DBPreset).filter(DBPreset.is_active == True), DBPreset, user_id).first()
    return {"presets": [{"id": row.id, "name": row.name, "version": row.version, "is_default": row.is_default, "is_active": row.is_active} for row in rows], "active": {"preset_id": active_row.id if active_row else (rows[0].id if rows else None)}}


@router.get("/presets/{preset_id}", response_model=PresetIn)
def get_preset(preset_id: str, db: Session = Depends(get_db), current_user: Optional[AuthUser] = Depends(get_current_user_sync)):
    user_id = current_user_id(current_user)
    ensure_default_preset_in_db(db, user_id)
    row = owner_only(db.query(DBPreset).filter(DBPreset.id == preset_id), DBPreset, user_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="preset not found")
    data = json.loads(row.config_json)
    return PresetIn(id=row.id, name=row.name, version=row.version, root=data.get("root", {}), meta=data.get("meta", {}))


@router.post("/presets", response_model=PresetIn)
def create_preset(name: str = "新预设", db: Session = Depends(get_db), current_user: Optional[AuthUser] = Depends(get_current_user_sync)):
    user_id = current_user_id(current_user)
    ensure_default_preset_in_db(db, user_id)
    data = prompts.default_preset(name=name)
    data["id"] = resolve_scoped_id(db, DBPreset, "id", data["id"], user_id)
    db.add(DBPreset(id=data["id"], name=name, version=1, config_json=json.dumps(data, ensure_ascii=False), is_active=False, is_default=False, user_id=user_id))
    db.commit()
    return PresetIn(**data)


@router.put("/presets/active")
def set_active(body: Dict[str, str] = Body(...), db: Session = Depends(get_db), current_user: Optional[AuthUser] = Depends(get_current_user_sync)):
    user_id = current_user_id(current_user)
    ensure_default_preset_in_db(db, user_id)
    target = owner_only(db.query(DBPreset).filter(DBPreset.id == body.get("preset_id")), DBPreset, user_id).first()
    if not target:
        raise HTTPException(status_code=404, detail="preset not found")
    owner_only(db.query(DBPreset), DBPreset, user_id).update({DBPreset.is_active: False})
    target.is_active = True
    db.commit()
    return {"preset_id": target.id, "is_default": target.is_default}


@router.put("/presets/{preset_id}")
def update_preset(preset_id: str, body: PresetIn, db: Session = Depends(get_db), current_user: Optional[AuthUser] = Depends(get_current_user_sync)):
    row = owner_only(db.query(DBPreset).filter(DBPreset.id == preset_id), DBPreset, current_user_id(current_user)).first()
    if not row:
        raise HTTPException(status_code=404, detail="not found")
    full_data = body.model_dump()
    full_data["id"] = preset_id
    row.name = body.name
    row.version = body.version
    row.config_json = json.dumps(full_data, ensure_ascii=False)
    db.commit()
    return full_data


@router.delete("/presets/{preset_id}")
def delete_preset(preset_id: str, db: Session = Depends(get_db), current_user: Optional[AuthUser] = Depends(get_current_user_sync)):
    row = owner_only(db.query(DBPreset).filter(DBPreset.id == preset_id), DBPreset, current_user_id(current_user)).first()
    if not row:
        raise HTTPException(status_code=404, detail="preset not found")
    if row.is_default:
        raise HTTPException(status_code=400, detail="Cannot delete default preset")
    db.delete(row)
    db.commit()
    return {"ok": True}


@router.post("/presets/import")
def import_any(body: Dict[str, Any], db: Session = Depends(get_db), current_user: Optional[AuthUser] = Depends(get_current_user_sync)):
    user_id = current_user_id(current_user)
    ensure_default_preset_in_db(db, user_id)
    data = prompts.import_preset(body.get("payload"), body.get("name_hint", "Imported"))
    data["id"] = resolve_scoped_id(db, DBPreset, "id", data["id"], user_id)
    db.add(DBPreset(id=data["id"], name=data["name"], version=1, config_json=json.dumps(data, ensure_ascii=False), is_default=False, user_id=user_id))
    db.commit()
    return data
