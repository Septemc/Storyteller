from __future__ import annotations
import json
import uuid
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from ..db.base import get_db
from ..db.models import DBPreset
from ..core import prompts

router = APIRouter()


class PresetIn(BaseModel):
    id: Optional[str] = None
    name: str = Field(default="未命名预设")
    version: int = 1
    root: Dict[str, Any]
    meta: Dict[str, Any] = Field(default_factory=dict)


@router.get("/presets")
def list_presets(db: Session = Depends(get_db)):
    rows = db.query(DBPreset).all()
    active_row = db.query(DBPreset).filter(DBPreset.is_active == True).first()

    out_list = []
    for r in rows:
        out_list.append({"id": r.id, "name": r.name, "version": r.version})

    return {
        "presets": out_list,
        "active": {"preset_id": active_row.id} if active_row else None
    }


@router.get("/presets/{preset_id}", response_model=PresetIn)
def get_preset(preset_id: str, db: Session = Depends(get_db)):
    row = db.query(DBPreset).filter(DBPreset.id == preset_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="preset not found")

    # 数据库存的是 JSON 字符串，取出来转 dict
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
    # 生成默认数据结构
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

    # 如果是第一个，设为激活
    if db.query(DBPreset).count() == 1:
        db_obj.is_active = True
        db.commit()

    return data


@router.put("/presets/{preset_id}")
def update_preset(preset_id: str, body: PresetIn, db: Session = Depends(get_db)):
    row = db.query(DBPreset).filter(DBPreset.id == preset_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="not found")

    # 构建完整 JSON 结构存入
    full_data = body.model_dump()
    full_data["id"] = preset_id  # 确保 ID 一致

    row.name = body.name
    row.version = body.version
    row.config_json = json.dumps(full_data, ensure_ascii=False)
    db.commit()

    return full_data


@router.delete("/presets/{preset_id}")
def delete_preset(preset_id: str, db: Session = Depends(get_db)):
    row = db.query(DBPreset).filter(DBPreset.id == preset_id).first()
    if not row:
        raise HTTPException(status_code=404)

    db.delete(row)
    db.commit()
    return {"ok": True}


@router.put("/presets/active")
def set_active(body: Dict[str, str], db: Session = Depends(get_db)):
    preset_id = body.get("preset_id")
    # 1. 验证存在
    target = db.query(DBPreset).filter(DBPreset.id == preset_id).first()
    if not target:
        raise HTTPException(status_code=404, detail="preset not found")

    # 2. 全部置为 False
    db.query(DBPreset).update({DBPreset.is_active: False})
    # 3. 目标置为 True
    target.is_active = True
    db.commit()

    return {"preset_id": target.id}


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