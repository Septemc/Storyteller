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

# 修改 routes_characters.py 中的 import_characters 函数
@router.post("/characters/import")
def import_characters(
        payload: Any = Body(...),
        db: Session = Depends(get_db)
):
    """
    [重构] 透明模式导入：不再拆分字段，原样保存
    """
    items = payload if isinstance(payload, list) else [payload]
    imported_count = 0

    for item in items:
        # 获取 ID，如果没有则生成
        char_id = item.get("character_id") or f"NPC_{int(time.time() * 1000)}"

        # 提取用于列表快速预览的基础信息 (取 tab_basic 或 basic)
        basic_info = item.get("tab_basic", item.get("basic", {}))

        character_data = {
            "character_id": char_id,
            "type": item.get("type", "npc"),
            "template_id": item.get("template_id", "system_default"),
            "data_json": json.dumps(item, ensure_ascii=False),  # 保存全量原始数据
            "basic_json": json.dumps(basic_info, ensure_ascii=False)  # 仅用于列表搜索和快速显示
        }

        # 执行保存
        existing = db.query(models.Character).filter_by(character_id=char_id).first()
        if existing:
            for k, v in character_data.items(): setattr(existing, k, v)
        else:
            db.add(models.Character(**character_data))
        imported_count += 1

    db.commit()
    return {"message": f"成功按照原始结构导入 {imported_count} 个角色。"}

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


@router.get("/characters/{character_id}")
def get_character(character_id: str, db: Session = Depends(get_db)):
    """
    [重构] 获取角色：返回扁平化的原始数据对象
    """
    ch = db.query(models.Character).filter_by(character_id=character_id).first()
    if not ch:
        raise HTTPException(status_code=404, detail="角色不存在")

    # 1. 解析原始全量数据
    try:
        full_data = json.loads(ch.data_json) if ch.data_json else {}
    except:
        full_data = {}

    # 2. 确保元数据在根级别，供前端 UI 使用
    full_data["character_id"] = ch.character_id
    full_data["type"] = ch.type
    full_data["template_id"] = ch.template_id or "system_default"

    # 直接返回 Dict，跳过 CharacterBase 的结构限制，实现路径完全对齐
    return full_data


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


@router.delete("/characters/clear_all")
def clear_all_characters(db: Session = Depends(get_db)):
    """
    [新增] 清空角色库中的所有数据
    """
    try:
        # 使用 SQLAlchemy 的 delete 方法快速清空表
        num_deleted = db.query(models.Character).delete(synchronize_session=False)
        db.commit()
        return {"message": f"成功清空角色库，共删除 {num_deleted} 个角色。", "count": num_deleted}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"清空失败: {str(e)}")


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
