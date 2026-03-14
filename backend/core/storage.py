"""DB-backed configuration access.

重构说明：
不再使用 GlobalSetting 存储巨型 JSON。
改为直接查询 DBPreset / DBLLMConfig 实体表，以确保与 Route 层的数据一致性。
"""

from __future__ import annotations

import json
from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session
from ..db import models
from .tenant import owner_only, owner_or_public

# --- Helper ---

def _parse_preset_config(json_str: str) -> Dict[str, Any]:
    try:
        return json.loads(json_str)
    except Exception:
        return {}

# --- LLM Config Access ---

def list_llm_configs(db: Session, user_id: Optional[str] = None) -> List[Dict[str, Any]]:
    """从 DBLLMConfig 表读取所有配置"""
    rows = owner_or_public(db.query(models.DBLLMConfig), models.DBLLMConfig, user_id).all()
    rows = sorted(rows, key=lambda row: (getattr(row, "user_id", None) != user_id, row.name or row.id))
    out = []
    for r in rows:
        out.append({
            "id": r.id,
            "name": r.name,
            "base_url": r.base_url,
            "api_key": r.api_key,
            "stream": r.stream,
            "default_model": r.default_model,
            "is_active": r.is_active
        })
    return out

def get_active_llm_config(db: Session, user_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """获取当前激活的 LLM 配置 (详细信息)"""
    query = owner_or_public(
        db.query(models.DBLLMConfig).filter(models.DBLLMConfig.is_active == True),
        models.DBLLMConfig,
        user_id,
    )
    rows = query.all()
    row = next((item for item in rows if getattr(item, "user_id", None) == user_id), None)
    if row is None:
        row = next((item for item in rows if getattr(item, "user_id", None) is None), None)
    
    if not row:
        rows = owner_or_public(db.query(models.DBLLMConfig), models.DBLLMConfig, user_id).all()
        row = next((item for item in rows if getattr(item, "user_id", None) == user_id), None)
        if row is None:
            row = next((item for item in rows if getattr(item, "user_id", None) is None), None)

    if not row:
        return None

    return {
        "id": row.id,
        "name": row.name,
        "base_url": row.base_url,
        "api_key": row.api_key,
        "stream": row.stream,
        "default_model": row.default_model,
    }

def get_llm_active(db: Session, user_id: Optional[str] = None) -> Dict[str, Any]:
    """获取当前激活的简要信息 (供 orchestrator 判断 model)"""
    cfg = get_active_llm_config(db, user_id)
    if not cfg:
        return {"config_id": None, "model": None}

    return {
        "config_id": cfg["id"],
        "model": cfg.get("default_model")
    }


# --- Preset Access ---

def list_presets(db: Session, user_id: Optional[str] = None) -> List[Dict[str, Any]]:
    """从 DBPreset 表读取所有预设元数据"""
    rows = owner_only(db.query(models.DBPreset), models.DBPreset, user_id).all()
    out = []
    for r in rows:
        # 注意：这里不解析庞大的 config_json，只返回列表所需的元数据
        out.append({
            "id": r.id,
            "name": r.name,
            "version": r.version,
            "is_active": r.is_active
        })
    return out

def get_active_preset(db: Session, user_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """获取当前激活的预设 (包含完整的 root 树结构)"""
    query = owner_only(
        db.query(models.DBPreset).filter(models.DBPreset.is_active == True),
        models.DBPreset,
        user_id,
    )
    row = query.first()
    
    if not row:
        query = owner_only(db.query(models.DBPreset), models.DBPreset, user_id)
        row = query.first()

    if not row:
        return None

    data = _parse_preset_config(row.config_json)

    return {
        "id": row.id,
        "name": row.name,
        "version": row.version,
        "root": data.get("root", {}),
        "meta": data.get("meta", {})
    }

# --- Regex Profile Access ---

def get_active_regex(db: Session, user_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """获取当前激活的正则配置"""
    query = owner_only(
        db.query(models.DBRegexProfile).filter(models.DBRegexProfile.is_active == True),
        models.DBRegexProfile,
        user_id,
    )
    row = query.first()
    
    if not row:
        query = owner_only(
            db.query(models.DBRegexProfile).filter(models.DBRegexProfile.is_default == True),
            models.DBRegexProfile,
            user_id,
        )
        row = query.first()
    
    if not row:
        return None
    
    config = _parse_preset_config(row.config_json) if row.config_json else {}
    
    return {
        "id": row.id,
        "name": row.name,
        "version": row.version,
        "is_default": row.is_default,
        "config_json": config
    }

# --- Deprecated / Compatibility ---
# 下面的 set_ 方法在基于 Table 的架构中通常由 Route 直接处理 DB 操作。
# 这里保留空实现或抛错，防止旧代码调用报错。

def save_llm_configs(db: Session, configs: List[Dict[str, Any]]) -> None:
    pass # 实际上不应该被调用，Route 应该直接操作 DB

def save_presets(db: Session, presets: List[Dict[str, Any]]) -> None:
    pass
