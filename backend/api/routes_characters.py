import time
import json
import os
from pathlib import Path
from typing import List, Optional, Any, Dict

from fastapi import APIRouter, Depends, HTTPException, Query, Body
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..db.base import get_db
from ..db import models

router = APIRouter()

# --- 配置文件加载逻辑 ---
CONFIG_PATH = Path(__file__).parent.parent / "mapping_config.json"


def load_mapping_config() -> Dict[str, List[str]]:
    if CONFIG_PATH.exists():
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading mapping config: {e}")
    return {}


def get_value_by_path(obj: Any, path: str) -> Any:
    """支持多级路径解析，如 'basic.name' 或 'data.stats.hp'"""
    if not path or not isinstance(obj, dict):
        return None
    parts = path.split('.')
    current = obj
    for part in parts:
        if isinstance(current, dict) and part in current:
            current = current[part]
        else:
            return None
    return current


# --- Pydantic Models ---
class CharacterBase(BaseModel):
    character_id: str
    type: str = "npc"
    template_id: str = "system_default"
    data: Dict[str, Any] = {}

    # 兼容各分类字段
    basic: Dict[str, Any] = {}
    knowledge: Dict[str, Any] = {}
    secrets: Dict[str, Any] = {}
    attributes: Dict[str, Any] = {}
    relations: Dict[str, Any] = {}
    equipment: List[Dict[str, Any]] = []
    items: List[Dict[str, Any]] = []
    skills: List[Dict[str, Any]] = []
    fortune: Dict[str, Any] = {}


class CharacterListItem(BaseModel):
    character_id: str
    type: str
    basic: Dict[str, Any] = {}


class CharacterListResponse(BaseModel):
    items: List[CharacterListItem]


# --- API Routes ---

@router.post("/characters/import")
def import_characters(
        payload: Any = Body(...),
        db: Session = Depends(get_db)
):
    """
    基于外部配置文件的动态批量导入。
    尽可能匹配所有路径，确保数据在不同模板下都能正确显示。
    """
    items = payload if isinstance(payload, list) else [payload]
    mapping_cfg = load_mapping_config()
    imported_count = 0

    for item in items:
        char_id = item.get("character_id") or f"NPC_{int(time.time() * 1000)}"

        # 基础元数据
        character_data = {
            "character_id": char_id,
            "type": item.get("type", "npc"),
            "template_id": item.get("template_id", "system_default"),
            "data_json": json.dumps(item, ensure_ascii=False)  # 原始全量快照
        }

        # 根据配置文件执行多路径动态匹配
        for db_field, potential_paths in mapping_cfg.items():
            db_col = f"{db_field}_json"
            matched_val = None

            # 尝试所有可能的路径，找到第一个匹配项
            for path in potential_paths:
                val = get_value_by_path(item, path)
                if val is not None:
                    matched_val = val
                    break

            # 如果匹配到数据，则序列化存储；否则存入对应的默认空结构
            if matched_val is not None:
                character_data[db_col] = json.dumps(matched_val, ensure_ascii=False)
            else:
                default_val = [] if db_field in ["equipment", "items", "skills"] else {}
                character_data[db_col] = json.dumps(default_val, ensure_ascii=False)

        # 执行 Upsert 逻辑
        existing = db.query(models.Character).filter_by(character_id=char_id).first()
        if existing:
            for key, value in character_data.items():
                setattr(existing, key, value)
        else:
            new_char = models.Character(**character_data)
            db.add(new_char)

        imported_count += 1

    db.commit()
    return {"message": f"成功导入 {imported_count} 个角色，已应用动态路径匹配。"}


@router.get("/characters/export/all")
def export_all_characters(db: Session = Depends(get_db)):
    """
    [新增] 导出所有角色的全量数据
    """
    chars = db.query(models.Character).all()
    results = []
    for ch in chars:
        # 复用 get_character 的解析逻辑
        full_data = json.loads(ch.data_json) if ch.data_json else {}
        full_data["character_id"] = ch.character_id
        full_data["type"] = ch.type
        full_data["template_id"] = ch.template_id or "system_default"
        results.append(full_data)
    return results


@router.get("/characters/{character_id}", response_model=CharacterBase)
def get_character(character_id: str, db: Session = Depends(get_db)):
    ch = db.query(models.Character).filter_by(character_id=character_id).first()
    if not ch:
        raise HTTPException(status_code=404, detail="角色不存在")

    def safe_json(val, default):
        try:
            return json.loads(val) if val else default
        except:
            return default

    # 获取全量快照作为数据池
    full_pool = safe_json(ch.data_json, {})

    # 返回组装好的对象，前端 template 会根据 path 从这里提取数据
    return CharacterBase(
        character_id=ch.character_id,
        type=ch.type,
        template_id=ch.template_id or "system_default",
        data=full_pool,
        basic=safe_json(ch.basic_json, {}),
        knowledge=safe_json(ch.knowledge_json, {}),
        secrets=safe_json(ch.secrets_json, {}),
        attributes=safe_json(ch.attributes_json, {}),
        relations=safe_json(ch.relations_json, {}),
        equipment=safe_json(ch.equipment_json, []),
        items=safe_json(ch.items_json, []),
        skills=safe_json(ch.skills_json, []),
        fortune=safe_json(ch.fortune_json, {})
    )


@router.get("/characters", response_model=CharacterListResponse)
def list_characters(q: Optional[str] = Query(None), db: Session = Depends(get_db)):
    query = db.query(models.Character)
    if q:
        query = query.filter(models.Character.character_id.like(f"%{q}%") | models.Character.basic_json.like(f"%{q}%"))
    rows = query.all()

    return CharacterListResponse(items=[
        CharacterListItem(
            character_id=r.character_id,
            type=r.type,
            basic=json.loads(r.basic_json) if r.basic_json else {}
        ) for r in rows
    ])


@router.put("/characters/{character_id}")
def update_character(character_id: str, payload: CharacterBase, db: Session = Depends(get_db)):
    ch = db.query(models.Character).filter_by(character_id=character_id).first()
    if not ch: raise HTTPException(404)

    ch.type = payload.type
    ch.template_id = payload.template_id
    ch.data_json = json.dumps(payload.data, ensure_ascii=False)
    ch.basic_json = json.dumps(payload.basic, ensure_ascii=False)
    ch.knowledge_json = json.dumps(payload.knowledge, ensure_ascii=False)
    ch.secrets_json = json.dumps(payload.secrets, ensure_ascii=False)
    ch.attributes_json = json.dumps(payload.attributes, ensure_ascii=False)
    ch.relations_json = json.dumps(payload.relations, ensure_ascii=False)
    ch.equipment_json = json.dumps(payload.equipment, ensure_ascii=False)
    ch.items_json = json.dumps(payload.items, ensure_ascii=False)
    ch.skills_json = json.dumps(payload.skills, ensure_ascii=False)
    ch.fortune_json = json.dumps(payload.fortune, ensure_ascii=False)

    db.commit()
    return payload


@router.delete("/characters/{character_id}")
def delete_character(character_id: str, db: Session = Depends(get_db)):
    ch = db.query(models.Character).filter_by(character_id=character_id).first()
    if not ch: raise HTTPException(404)
    db.delete(ch)
    db.commit()
    return {"status": "ok"}