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

router = APIRouter()

DEFAULT_PRESET_PATH = Path(__file__).parent.parent.parent / "data" / "default_preset.json"


def load_default_preset() -> Dict[str, Any]:
    if DEFAULT_PRESET_PATH.exists():
        with open(DEFAULT_PRESET_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return prompts.default_preset("默认预设")


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
def list_presets(db: Session = Depends(get_db)):
    default_preset = load_default_preset()
    
    rows = db.query(DBPreset).all()
    active_row = db.query(DBPreset).filter(DBPreset.is_active == True).first()

    out_list = [
        PresetListItem(
            id=default_preset["id"],
            name=default_preset["name"],
            version=default_preset.get("version", 1),
            is_default=True,
            is_active=active_row is None
        ).model_dump()
    ]

    for r in rows:
        out_list.append({
            "id": r.id,
            "name": r.name,
            "version": r.version,
            "is_default": False,
            "is_active": r.is_active
        })

    return {
        "presets": out_list,
        "active": {"preset_id": active_row.id} if active_row else {"preset_id": default_preset["id"]}
    }


@router.get("/presets/{preset_id}", response_model=PresetIn)
def get_preset(preset_id: str, db: Session = Depends(get_db)):
    default_preset = load_default_preset()
    
    if preset_id == default_preset["id"]:
        return {
            "id": default_preset["id"],
            "name": default_preset["name"],
            "version": default_preset.get("version", 1),
            "root": default_preset.get("root", {}),
            "meta": default_preset.get("meta", {})
        }
    
    row = db.query(DBPreset).filter(DBPreset.id == preset_id).first()
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
def create_preset(name: str = "新预设", db: Session = Depends(get_db)):
    data = prompts.default_preset(name=name)
    pid = data["id"]

    db_obj = DBPreset(
        id=pid,
        name=name,
        version=1,
        config_json=json.dumps(data, ensure_ascii=False),
        is_active=False
    )
    db.add(db_obj)
    db.commit()

    return data


@router.put("/presets/active")
def set_active(body: Dict[str, str] = Body(...), db: Session = Depends(get_db)):
    default_preset = load_default_preset()
    preset_id = body.get("preset_id")
    
    if preset_id == default_preset["id"]:
        db.query(DBPreset).update({DBPreset.is_active: False})
        db.commit()
        return {"preset_id": preset_id, "is_default": True}
    
    target = db.query(DBPreset).filter(DBPreset.id == preset_id).first()
    if not target:
        raise HTTPException(status_code=404, detail="preset not found")

    db.query(DBPreset).update({DBPreset.is_active: False})
    target.is_active = True
    db.commit()

    return {"preset_id": target.id, "is_default": False}


@router.put("/presets/{preset_id}")
def update_preset(preset_id: str, body: PresetIn, db: Session = Depends(get_db)):
    default_preset = load_default_preset()
    
    if preset_id == default_preset["id"]:
        raise HTTPException(status_code=400, detail="Cannot modify default preset")
    
    row = db.query(DBPreset).filter(DBPreset.id == preset_id).first()
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
def delete_preset(preset_id: str, db: Session = Depends(get_db)):
    default_preset = load_default_preset()
    
    if preset_id == default_preset["id"]:
        raise HTTPException(status_code=400, detail="Cannot delete default preset")
    
    row = db.query(DBPreset).filter(DBPreset.id == preset_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="preset not found")

    db.delete(row)
    db.commit()
    return {"ok": True}


@router.post("/presets/import")
def import_any(body: Dict[str, Any], db: Session = Depends(get_db)):
    payload = body.get("payload")
    name_hint = body.get("name_hint", "Imported")

    data = prompts.import_preset(payload, name_hint)
    pid = data["id"]

    db_obj = DBPreset(
        id=pid,
        name=name_hint,
        version=1,
        config_json=json.dumps(data, ensure_ascii=False)
    )
    db.add(db_obj)
    db.commit()
    return data
