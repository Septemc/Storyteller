import time
from typing import List, Optional, Any, Dict

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..db.base import get_db
from ..db import models

router = APIRouter()


class CharacterBase(BaseModel):
    character_id: str
    type: str = "npc"
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


@router.get("/characters", response_model=CharacterListResponse)
def list_characters(
    q: Optional[str] = Query(None, description="按名称或编号搜索"),
    db: Session = Depends(get_db),
) -> CharacterListResponse:
    import json

    query = db.query(models.Character)
    if q:
        like = f"%{q}%"
        query = query.filter(
            (models.Character.character_id.like(like))
            | (models.Character.basic_json.like(like))
        )
    rows = query.order_by(models.Character.character_id).all()

    items: List[CharacterListItem] = []
    for ch in rows:
        basic: Dict[str, Any] = {}
        if ch.basic_json:
            try:
                basic = json.loads(ch.basic_json)
            except Exception:
                basic = {}
        items.append(
            CharacterListItem(
                character_id=ch.character_id,
                type=ch.type,
                basic=basic,
            )
        )
    return CharacterListResponse(items=items)


@router.get("/characters/{character_id}", response_model=CharacterBase)
def get_character(character_id: str, db: Session = Depends(get_db)) -> CharacterBase:
    import json

    ch = (
        db.query(models.Character)
        .filter(models.Character.character_id == character_id)
        .first()
    )
    if not ch:
        raise HTTPException(status_code=404, detail="角色不存在。")

    def parse_or_empty(value: Optional[str], default: Any) -> Any:
        if not value:
            return default
        try:
            return json.loads(value)
        except Exception:
            return default

    return CharacterBase(
        character_id=ch.character_id,
        type=ch.type,
        basic=parse_or_empty(ch.basic_json, {}),
        knowledge=parse_or_empty(ch.knowledge_json, {}),
        secrets=parse_or_empty(ch.secrets_json, {}),
        attributes=parse_or_empty(ch.attributes_json, {}),
        relations=parse_or_empty(ch.relations_json, {}),
        equipment=parse_or_empty(ch.equipment_json, []),
        items=parse_or_empty(ch.items_json, []),
        skills=parse_or_empty(ch.skills_json, []),
        fortune=parse_or_empty(ch.fortune_json, {}),
    )


@router.post("/characters", response_model=CharacterBase)
def create_character(payload: CharacterBase, db: Session = Depends(get_db)) -> CharacterBase:
    import json

    existing = (
        db.query(models.Character)
        .filter(models.Character.character_id == payload.character_id)
        .first()
    )
    if existing:
        raise HTTPException(status_code=400, detail="角色编号已存在。")

    ch = models.Character(
        character_id=payload.character_id,
        type=payload.type,
        basic_json=json.dumps(payload.basic, ensure_ascii=False),
        knowledge_json=json.dumps(payload.knowledge, ensure_ascii=False),
        secrets_json=json.dumps(payload.secrets, ensure_ascii=False),
        attributes_json=json.dumps(payload.attributes, ensure_ascii=False),
        relations_json=json.dumps(payload.relations, ensure_ascii=False),
        equipment_json=json.dumps(payload.equipment, ensure_ascii=False),
        items_json=json.dumps(payload.items, ensure_ascii=False),
        skills_json=json.dumps(payload.skills, ensure_ascii=False),
        fortune_json=json.dumps(payload.fortune, ensure_ascii=False),
    )
    db.add(ch)
    db.commit()
    db.refresh(ch)
    return payload


@router.put("/characters/{character_id}", response_model=CharacterBase)
def update_character(
    character_id: str,
    payload: CharacterBase,
    db: Session = Depends(get_db),
) -> CharacterBase:
    import json

    ch = (
        db.query(models.Character)
        .filter(models.Character.character_id == character_id)
        .first()
    )
    if not ch:
        raise HTTPException(status_code=404, detail="角色不存在。")

    ch.type = payload.type
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


@router.post("/import")
def import_characters(
        payload: Any,  # 接收 List[Dict] 或 Dict
        db: Session = Depends(get_db)
):
    """
    批量导入角色。
    支持格式：单个对象 {...} 或 列表 [{...}, {...}]
    如果 character_id 为空，自动生成。
    如果 character_id 已存在，则覆盖（或根据需求跳过，这里演示覆盖更新）。
    """
    if isinstance(payload, dict):
        # 兼容 { "entries": [...] } 格式，或者单个人物对象
        if "entries" in payload and isinstance(payload["entries"], list):
            items = payload["entries"]
        else:
            items = [payload]
    elif isinstance(payload, list):
        items = payload
    else:
        raise HTTPException(status_code=400, detail="Invalid format. Expected JSON list or object.")

    imported_count = 0

    # 获取当前最大编号的简单的逻辑（可选），或者使用随机ID
    # 这里演示一个简单的 ID 生成器函数
    def generate_next_id():
        return f"NPC_{int(time.time() * 1000)}"

    for item in items:
        # 1. 提取或生成 ID
        char_id = item.get("character_id")
        if not char_id:
            char_id = generate_next_id()
            # 确保稍微错开时间避免重复
            time.sleep(0.001)

            # 2. 准备数据模型

        # 注意：前端发来的 JSON 子字段（如 basic, knowledge）可能是 dict，
        # 但数据库存的是 JSON string，需要 dumps。
        # 如果前端发来已经是 string 则不动。

        def ensure_json_string(val):
            if isinstance(val, (dict, list)):
                return json.dumps(val, ensure_ascii=False)
            return val if val else "{}"

        character_data = {
            "character_id": char_id,
            "type": item.get("type", "npc"),
            "basic_json": ensure_json_string(item.get("basic", {})),
            "knowledge_json": ensure_json_string(item.get("knowledge", {})),
            "secrets_json": ensure_json_string(item.get("secrets", {})),
            "attributes_json": ensure_json_string(item.get("attributes", {})),
            "relations_json": ensure_json_string(item.get("relations", {})),
            "equipment_json": ensure_json_string(item.get("equipment", [])),
            "items_json": ensure_json_string(item.get("items", [])),
            "skills_json": ensure_json_string(item.get("skills", [])),
            "fortune_json": ensure_json_string(item.get("fortune", {})),
            "meta_json": ensure_json_string(item.get("meta", {}))
        }

        # 3. 查找是否存在（Upsert 逻辑）
        existing = db.query(Character).filter(Character.character_id == char_id).first()
        if existing:
            for key, value in character_data.items():
                setattr(existing, key, value)
        else:
            new_char = Character(**character_data)
            db.add(new_char)

        imported_count += 1

    db.commit()
    return {"message": f"Successfully imported {imported_count} characters."}