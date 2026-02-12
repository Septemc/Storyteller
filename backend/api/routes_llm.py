from __future__ import annotations

import uuid
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from ..db.base import get_db
from ..db.models import DBLLMConfig
from ..core.llm_client import LLMError, list_models

router = APIRouter()


# --- Pydantic Models ---

class LLMConfigIn(BaseModel):
    id: Optional[str] = None
    name: str = Field(default="未命名配置")
    base_url: str
    api_key: str
    stream: bool = True
    default_model: Optional[str] = None


class LLMConfigOut(LLMConfigIn):
    id: str


class ActiveLLM(BaseModel):
    config_id: Optional[str] = None
    model: Optional[str] = None


class ListModelsReq(BaseModel):
    base_url: str
    api_key: str


# --- Routes ---

@router.get("/llm/configs")
def get_configs(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """获取所有配置列表以及当前激活的配置"""
    rows = db.query(DBLLMConfig).all()
    active_row = db.query(DBLLMConfig).filter(DBLLMConfig.is_active == True).first()

    configs_out = []
    for r in rows:
        configs_out.append({
            "id": r.id,
            "name": r.name,
            "base_url": r.base_url,
            "api_key": r.api_key,  # 注意：实际生产环境建议脱敏处理
            "stream": r.stream,
            "default_model": r.default_model,
        })

    active_data = {}
    if active_row:
        active_data = {
            "config_id": active_row.id,
            "model": active_row.default_model
        }

    return {
        "configs": configs_out,
        "active": active_data,
    }


@router.post("/llm/configs", response_model=LLMConfigOut)
def create_config(body: LLMConfigIn, db: Session = Depends(get_db)):
    """创建新的 LLM 配置"""
    # 1. 生成 ID
    cid = body.id
    if not cid:
        cid = f"llm_{uuid.uuid4().hex[:10]}"

    # 2. 创建数据库对象
    new_config = DBLLMConfig(
        id=cid,
        name=body.name,
        base_url=body.base_url,
        api_key=body.api_key,
        stream=body.stream,
        default_model=body.default_model,
        is_active=False  # 默认不激活，除非是第一个
    )

    db.add(new_config)
    db.commit()
    db.refresh(new_config)

    # 3. 如果这是数据库中唯一的配置，自动设为激活
    total_count = db.query(DBLLMConfig).count()
    if total_count == 1:
        new_config.is_active = True
        db.commit()
        db.refresh(new_config)

    return {
        "id": new_config.id,
        "name": new_config.name,
        "base_url": new_config.base_url,
        "api_key": new_config.api_key,
        "stream": new_config.stream,
        "default_model": new_config.default_model,
    }


@router.put("/llm/configs/{config_id}", response_model=LLMConfigOut)
def update_config(config_id: str, body: LLMConfigIn, db: Session = Depends(get_db)):
    """更新现有的 LLM 配置"""
    config = db.query(DBLLMConfig).filter(DBLLMConfig.id == config_id).first()
    if not config:
        raise HTTPException(status_code=404, detail="config not found")

    config.name = body.name
    config.base_url = body.base_url
    config.api_key = body.api_key
    config.stream = body.stream
    # 如果传了 default_model 则更新，没传保持原样或置空，视业务需求。这里假设跟随 body
    config.default_model = body.default_model

    db.commit()
    db.refresh(config)

    return {
        "id": config.id,
        "name": config.name,
        "base_url": config.base_url,
        "api_key": config.api_key,
        "stream": config.stream,
        "default_model": config.default_model,
    }


@router.delete("/llm/configs/{config_id}")
def delete_config(config_id: str, db: Session = Depends(get_db)):
    """删除配置"""
    config = db.query(DBLLMConfig).filter(DBLLMConfig.id == config_id).first()
    if not config:
        raise HTTPException(status_code=404, detail="config not found")

    was_active = config.is_active
    db.delete(config)
    db.commit()

    # 如果删除的是当前激活的配置，尝试回退到剩下列表的第一个
    if was_active:
        fallback = db.query(DBLLMConfig).first()
        if fallback:
            fallback.is_active = True
            db.commit()

    return {"ok": True}


@router.put("/llm/active")
def set_active(body: ActiveLLM, db: Session = Depends(get_db)):
    """设置当前激活的配置 ID 及选中的模型"""
    if not body.config_id:
        # 如果没有传 ID，视为清除激活状态
        db.query(DBLLMConfig).update({DBLLMConfig.is_active: False})
        db.commit()
        return {}

    # 1. 检查目标是否存在
    target = db.query(DBLLMConfig).filter(DBLLMConfig.id == body.config_id).first()
    if not target:
        raise HTTPException(status_code=404, detail="config not found")

    # 2. 将所有配置设为非激活
    db.query(DBLLMConfig).update({DBLLMConfig.is_active: False})

    # 3. 激活目标配置
    target.is_active = True

    # 4. 如果前端指定了模型，更新该配置的默认模型记忆
    if body.model:
        target.default_model = body.model

    db.commit()
    db.refresh(target)

    return {
        "config_id": target.id,
        "model": target.default_model
    }


@router.get("/llm/configs/{config_id}/models")
def get_models_for_config(config_id: str, db: Session = Depends(get_db)):
    """根据配置 ID 获取可用模型列表"""
    cfg = db.query(DBLLMConfig).filter(DBLLMConfig.id == config_id).first()
    if not cfg:
        raise HTTPException(status_code=404, detail="config not found")

    try:
        # 使用 core.llm_client 中的工具函数请求远程 API
        models = list_models(cfg.base_url or "", cfg.api_key or "")
    except LLMError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return {"models": models}


@router.post("/llm/models/list")
def list_models_by_credentials(body: ListModelsReq):
    """不保存配置，直接测试连接获取模型列表"""
    try:
        models = list_models(body.base_url, body.api_key)
    except LLMError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"models": models}