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

# --- Helper ---

def _parse_preset_config(json_str: str) -> Dict[str, Any]:
    try:
        return json.loads(json_str)
    except Exception:
        return {}

# --- LLM Config Access ---

def list_llm_configs(db: Session) -> List[Dict[str, Any]]:
    """从 DBLLMConfig 表读取所有配置"""
    rows = db.query(models.DBLLMConfig).all()
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

def get_active_llm_config(db: Session) -> Optional[Dict[str, Any]]:
    """获取当前激活的 LLM 配置 (详细信息)"""
    # 直接查询 is_active = True 的记录
    row = db.query(models.DBLLMConfig).filter(models.DBLLMConfig.is_active == True).first()
    if not row:
        # Fallback: 如果没有激活的，取第一个
        row = db.query(models.DBLLMConfig).first()

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

def get_llm_active(db: Session) -> Dict[str, Any]:
    """获取当前激活的简要信息 (供 orchestrator 判断 model)"""
    cfg = get_active_llm_config(db)
    if not cfg:
        return {"config_id": None, "model": None}

    return {
        "config_id": cfg["id"],
        "model": cfg.get("default_model") # Route中设定激活时会更新这个字段
    }


# --- Preset Access ---

def list_presets(db: Session) -> List[Dict[str, Any]]:
    """从 DBPreset 表读取所有预设元数据"""
    rows = db.query(models.DBPreset).all()
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

def get_active_preset(db: Session) -> Optional[Dict[str, Any]]:
    """获取当前激活的预设 (包含完整的 root 树结构)"""
    row = db.query(models.DBPreset).filter(models.DBPreset.is_active == True).first()
    if not row:
        row = db.query(models.DBPreset).first()

    if not row:
        return None

    # 解析 JSON
    data = _parse_preset_config(row.config_json)

    # 构造完整对象
    return {
        "id": row.id,
        "name": row.name,
        "version": row.version,
        "root": data.get("root", {}),
        "meta": data.get("meta", {})
    }

# --- Deprecated / Compatibility ---
# 下面的 set_ 方法在基于 Table 的架构中通常由 Route 直接处理 DB 操作。
# 这里保留空实现或抛错，防止旧代码调用报错。

def save_llm_configs(db: Session, configs: List[Dict[str, Any]]) -> None:
    pass # 实际上不应该被调用，Route 应该直接操作 DB

def save_presets(db: Session, presets: List[Dict[str, Any]]) -> None:
    pass