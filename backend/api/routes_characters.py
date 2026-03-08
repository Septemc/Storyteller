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
from ..core.auth import get_current_user, User as AuthUser

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


def extract_categorized_data(item: Dict[str, Any]) -> Dict[str, str]:
    """
    从角色数据中提取各个分类字段，并转换为 JSON 字符串
    支持 tab_xxx 和 xxx 两种命名格式
    """
    field_mapping = {
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
    
    result = {}
    meta_keys = {"character_id", "type", "template_id"}
    for db_field, source_fields in field_mapping.items():
        data = None
        for source in source_fields:
            if source in item:
                data = item[source]
                break
        if data is None and db_field == "basic_json":
            # 兼容旧结构：角色字段直接平铺在根对象（如 f_name, f_age）
            flat_fields = {
                k: v
                for k, v in item.items()
                if k not in meta_keys and not k.startswith("tab_")
            }
            if flat_fields:
                data = flat_fields

        if data is None:
            data = {}

        result[db_field] = json.dumps(data, ensure_ascii=False)
    return result


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
        db: Session = Depends(get_db),
        current_user: Optional[AuthUser] = Depends(get_current_user)
):
    """
    [重构] 透明模式导入：不再拆分字段，原样保存
    """
    if not current_user:
        raise HTTPException(status_code=401, detail="需要登录才能导入角色数据")
    
    user_id = current_user.user_id
    items = payload if isinstance(payload, list) else [payload]
    imported_count = 0

    for item in items:
        char_id = item.get("character_id") or f"NPC_{int(time.time() * 1000)}"

        # 提取各个分类字段的数据
        categorized = extract_categorized_data(item)
        basic_info = item.get("tab_basic", item.get("basic", {}))

        character_data = {
            "character_id": char_id,
            "type": item.get("type", "npc"),
            "template_id": item.get("template_id", "system_default"),
            "data_json": json.dumps(item, ensure_ascii=False),
            **categorized
        }

        # 执行保存
        existing_query = db.query(models.Character).filter_by(character_id=char_id)
        existing_query = existing_query.filter(models.Character.user_id == user_id)
        existing = existing_query.first()
        
        if existing:
            for k, v in character_data.items(): setattr(existing, k, v)
        else:
            db.add(models.Character(**character_data))
        imported_count += 1

    db.commit()
    return {"message": f"成功按照原始结构导入 {imported_count} 个角色。"}

@router.get("/characters/export/all")
def export_all_characters(db: Session = Depends(get_db), current_user: Optional[AuthUser] = Depends(get_current_user)):
    """
    [新增] 导出所有角色的全量数据
    """
    if not current_user:
        raise HTTPException(status_code=401, detail="需要登录才能导出角色数据")
    
    user_id = current_user.user_id
    query = db.query(models.Character).filter(models.Character.user_id == user_id)
    chars = query.all()
    results = []
    for ch in chars:
        full_data = json.loads(ch.data_json) if ch.data_json else {}
        full_data["character_id"] = ch.character_id
        full_data["type"] = ch.type
        full_data["template_id"] = ch.template_id or "system_default"
        results.append(full_data)
    return results


@router.get("/characters/{character_id}")
def get_character(character_id: str, db: Session = Depends(get_db), current_user: Optional[AuthUser] = Depends(get_current_user)):
    """
    [重构] 获取角色：自动重构完整数据，包括所有 tab 字段
    """
    if not current_user:
        raise HTTPException(status_code=401, detail="需要登录才能访问角色数据")
    
    user_id = current_user.user_id
    query = db.query(models.Character).filter_by(character_id=character_id).filter(models.Character.user_id == user_id)
    ch = query.first()
    
    if not ch:
        raise HTTPException(status_code=404, detail="角色不存在")

    # 从各个分类字段重构完整数据（优先用分类字段，备选 data_json）
    full_data = {}
    
    # 尝试从 data_json 读取基础结构
    try:
        if ch.data_json:
            full_data = json.loads(ch.data_json)
    except:
        pass
    
    # 补充各个分类字段的数据，优先级高于 data_json
    field_mapping = {
        "tab_basic": ch.basic_json,
        "tab_knowledge": ch.knowledge_json,
        "tab_secrets": ch.secrets_json,
        "tab_attributes": ch.attributes_json,
        "tab_relations": ch.relations_json,
        "tab_equipment": ch.equipment_json,
        "tab_items": ch.items_json,
        "tab_skills": ch.skills_json,
        "tab_fortune": ch.fortune_json,
    }
    
    for field_name, field_data in field_mapping.items():
        # 如果分类字段有数据，就用它（覆盖 data_json 中的同名字段）
        if field_data:
            try:
                full_data[field_name] = json.loads(field_data)
            except:
                pass
        # 如果分类字段为 NULL 但 data_json 中也没有对应字段，添加空对象
        elif field_name not in full_data:
            full_data[field_name] = {}

    # 添加元数据
        full_data = {}

    full_data["character_id"] = ch.character_id
    full_data["type"] = ch.type
    full_data["template_id"] = ch.template_id or "system_default"

    return full_data


@router.get("/characters", response_model=CharacterListResponse)
def list_characters(q: Optional[str] = Query(None), db: Session = Depends(get_db), current_user: Optional[AuthUser] = Depends(get_current_user)):
    user_id = current_user.user_id if current_user else None
    query = db.query(models.Character)
    if user_id:
        query = query.filter(models.Character.user_id == user_id)
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
def clear_all_characters(db: Session = Depends(get_db), current_user: Optional[AuthUser] = Depends(get_current_user)):
    """
    [新增] 清空角色库中的所有数据
    """
    user_id = current_user.user_id if current_user else None
    try:
        query = db.query(models.Character)
        if user_id:
            query = query.filter(models.Character.user_id == user_id)
        num_deleted = query.delete(synchronize_session=False)
        db.commit()
        return {"message": f"成功清空角色库，共删除 {num_deleted} 个角色。", "count": num_deleted}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"清空失败: {str(e)}")


@router.put("/characters/{character_id}")
def update_character(character_id: str, payload: Any = Body(...), db: Session = Depends(get_db)):
    """
    [重构] 更新角色：使用透明模式，接收原始扁平数据并原样保存
    前端发送的数据格式: { character_id, type, template_id, tab_basic, tab_stats, ... }
    """
    ch = db.query(models.Character).filter_by(character_id=character_id).first()
    if not ch:
        raise HTTPException(404, detail="角色不存在")
def update_character(character_id: str, payload: CharacterBase, db: Session = Depends(get_db), current_user: Optional[AuthUser] = Depends(get_current_user)):
    user_id = current_user.user_id if current_user else None
    query = db.query(models.Character).filter_by(character_id=character_id)
    if user_id:
        query = query.filter(models.Character.user_id == user_id)
    ch = query.first()
    if not ch: raise HTTPException(404)

    # 提取各个分类字段的数据
    categorized = extract_categorized_data(payload)
    
    # 更新全量原始数据
    ch.data_json = json.dumps(payload, ensure_ascii=False)
    
    # 更新各个分类字段
    for field, value in categorized.items():
        setattr(ch, field, value)
    
    # 更新元数据
    ch.type = payload.get("type", ch.type)
    ch.template_id = payload.get("template_id", ch.template_id)
    
    db.commit()
    
    # 返回完整的角色数据（包含元数据）
    result = json.loads(ch.data_json) if ch.data_json else {}
    result["character_id"] = ch.character_id
    result["type"] = ch.type
    result["template_id"] = ch.template_id
    return result


@router.delete("/characters/{character_id}")
def delete_character(character_id: str, db: Session = Depends(get_db), current_user: Optional[AuthUser] = Depends(get_current_user)):
    user_id = current_user.user_id if current_user else None
    query = db.query(models.Character).filter_by(character_id=character_id)
    if user_id:
        query = query.filter(models.Character.user_id == user_id)
    ch = query.first()
    if not ch: raise HTTPException(404)
    db.delete(ch)
    db.commit()
    return {"status": "ok"}
