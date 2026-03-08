from __future__ import annotations
import json
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Body
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from ..db.base import get_db
from ..db.models import DBPreset
from ..core import prompts
from ..core.auth import get_current_user, User as AuthUser

router = APIRouter()

DEFAULT_PRESET_PATH = Path(__file__).parent.parent.parent / "data" / "default_preset.json"
DEFAULT_PRESET_ID = "preset_default"


def load_default_preset_from_file() -> Dict[str, Any]:
    if DEFAULT_PRESET_PATH.exists():
        with open(DEFAULT_PRESET_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return prompts.default_preset("默认预设")


def ensure_default_preset_in_db(db: Session, user_id: Optional[int] = None) -> DBPreset:
    query = db.query(DBPreset).filter(DBPreset.is_default == True)
    if user_id:
        query = query.filter(DBPreset.user_id == user_id)
    else:
        # 未登录用户只能访问系统默认配置
        query = query.filter(DBPreset.user_id == None)
    default_preset = query.first()
    
    if default_preset:
        return default_preset
    
    file_preset = load_default_preset_from_file()
    
    preset_id = file_preset.get("id", DEFAULT_PRESET_ID)
    
    existing_query = db.query(DBPreset).filter(DBPreset.id == preset_id)
    if user_id:
        existing_query = existing_query.filter(DBPreset.user_id == user_id)
    else:
        existing_query = existing_query.filter(DBPreset.user_id == None)
    existing = existing_query.first()
    if existing:
        existing.is_default = True
        db.commit()
        return existing
    
    default_preset = DBPreset(
        id=preset_id,
        name=file_preset.get("name", "默认预设"),
        version=file_preset.get("version", 1),
        is_active=True,
        is_default=True,
        config_json=json.dumps(file_preset, ensure_ascii=False),
        user_id=user_id,
    )
    db.add(default_preset)
    db.commit()
    db.refresh(default_preset)
    
    return default_preset


class PresetIn(BaseModel):
    id: Optional[str] = None
    name: str = Field(default="未命名预设")
    version: int = 1
    root: Dict[str, Any]
    meta: Dict[str, Any] = Field(default_factory=dict)


class PresetListItem(BaseModel):
    id: str
    name: str
    version: int
    is_default: bool = False
    is_active: bool = False


@router.get("/presets")
def list_presets(db: Session = Depends(get_db), current_user: Optional[AuthUser] = Depends(get_current_user)):
    user_id = current_user.user_id if current_user else None
    ensure_default_preset_in_db(db, user_id)
    
    query = db.query(DBPreset)
    if user_id:
        query = query.filter(DBPreset.user_id == user_id)
    rows = query.order_by(DBPreset.is_default.desc(), DBPreset.created_at.asc()).all()
    
    active_query = db.query(DBPreset).filter(DBPreset.is_active == True)
    if user_id:
        active_query = active_query.filter(DBPreset.user_id == user_id)
    active_row = active_query.first()

    out_list = []
    for r in rows:
        out_list.append({
            "id": r.id,
            "name": r.name,
            "version": r.version,
            "is_default": r.is_default,
            "is_active": r.is_active
        })

    return {
        "presets": out_list,
        "active": {"preset_id": active_row.id if active_row else (rows[0].id if rows else None)}
    }


@router.get("/presets/{preset_id}", response_model=PresetIn)
def get_preset(preset_id: str, db: Session = Depends(get_db), current_user: Optional[AuthUser] = Depends(get_current_user)):
    user_id = current_user.user_id if current_user else None
    ensure_default_preset_in_db(db, user_id)
    
    query = db.query(DBPreset).filter(DBPreset.id == preset_id)
    if user_id:
        query = query.filter(DBPreset.user_id == user_id)
    row = query.first()
    if not row:
        raise HTTPException(status_code=404, detail="preset not found")

    data = json.loads(row.config_json)
    return {
        "id": row.id,
        "name": row.name,
        "version": row.version,
        "root": data.get("root", {}),
        "meta": data.get("meta", {})
    }


@router.post("/presets", response_model=PresetIn)
def create_preset(name: str = "新预设", db: Session = Depends(get_db), current_user: Optional[AuthUser] = Depends(get_current_user)):
    user_id = current_user.user_id if current_user else None
    ensure_default_preset_in_db(db, user_id)
    
    data = prompts.default_preset(name=name)
    pid = data["id"]

    db_obj = DBPreset(
        id=pid,
        name=name,
        version=1,
        config_json=json.dumps(data, ensure_ascii=False),
        is_active=False,
        is_default=False,
        user_id=user_id,
    )
    db.add(db_obj)
    db.commit()

    return data


@router.put("/presets/active")
def set_active(body: Dict[str, str] = Body(...), db: Session = Depends(get_db), current_user: Optional[AuthUser] = Depends(get_current_user)):
    user_id = current_user.user_id if current_user else None
    ensure_default_preset_in_db(db, user_id)
    
    preset_id = body.get("preset_id")
    
    query = db.query(DBPreset).filter(DBPreset.id == preset_id)
    if user_id:
        query = query.filter(DBPreset.user_id == user_id)
    target = query.first()
    if not target:
        raise HTTPException(status_code=404, detail="preset not found")

    update_query = db.query(DBPreset)
    if user_id:
        update_query = update_query.filter(DBPreset.user_id == user_id)
    update_query.update({DBPreset.is_active: False})
    target.is_active = True
    db.commit()

    return {"preset_id": target.id, "is_default": target.is_default}


@router.put("/presets/{preset_id}")
def update_preset(preset_id: str, body: PresetIn, db: Session = Depends(get_db), current_user: Optional[AuthUser] = Depends(get_current_user)):
    user_id = current_user.user_id if current_user else None
    ensure_default_preset_in_db(db, user_id)
    
    query = db.query(DBPreset).filter(DBPreset.id == preset_id)
    if user_id:
        query = query.filter(DBPreset.user_id == user_id)
    row = query.first()
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
def delete_preset(preset_id: str, db: Session = Depends(get_db), current_user: Optional[AuthUser] = Depends(get_current_user)):
    user_id = current_user.user_id if current_user else None
    ensure_default_preset_in_db(db, user_id)
    
    query = db.query(DBPreset).filter(DBPreset.id == preset_id)
    if user_id:
        query = query.filter(DBPreset.user_id == user_id)
    row = query.first()
    if not row:
        raise HTTPException(status_code=404, detail="preset not found")

    if row.is_default:
        raise HTTPException(status_code=400, detail="Cannot delete default preset")

    db.delete(row)
    db.commit()
    return {"ok": True}


@router.post("/presets/import")
def import_any(body: Dict[str, Any], db: Session = Depends(get_db), current_user: Optional[AuthUser] = Depends(get_current_user)):
    user_id = current_user.user_id if current_user else None
    ensure_default_preset_in_db(db, user_id)
    
    payload = body.get("payload")
    name_hint = body.get("name_hint", "Imported")

    data = prompts.import_preset(payload, name_hint)
    pid = data["id"]

    db_obj = DBPreset(
        id=pid,
        name=name_hint,
        version=1,
        config_json=json.dumps(data, ensure_ascii=False),
        is_default=False,
        user_id=user_id,
    )
    db.add(db_obj)
    db.commit()
    return data
