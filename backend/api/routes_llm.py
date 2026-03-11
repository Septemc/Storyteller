from __future__ import annotations

import logging
import uuid
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from ..db.base import get_db
from ..db.models import DBLLMConfig
from ..core.llm_client import LLMError, list_models
from ..core.auth import get_current_user, User as AuthUser
from ..core.tenant import current_user_id, owner_only

router = APIRouter()
logger = logging.getLogger(__name__)


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
def get_configs(db: Session = Depends(get_db), current_user: Optional[AuthUser] = Depends(get_current_user)) -> Dict[str, Any]:
    """获取所有配置列表以及当前激活的配置"""
    if not current_user:
        raise HTTPException(status_code=401, detail="需要登录才能访问LLM配置")
    
    user_id = current_user_id(current_user)
    query = owner_only(db.query(DBLLMConfig), DBLLMConfig, user_id)
    rows = query.all()
    
    active_query = owner_only(
        db.query(DBLLMConfig).filter(DBLLMConfig.is_active == True),
        DBLLMConfig,
        user_id,
    )
    active_row = active_query.first()

    configs_out = []
    for r in rows:
        configs_out.append({
            "id": r.id,
            "name": r.name,
            "base_url": r.base_url,
            "api_key": r.api_key,
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
def create_config(body: LLMConfigIn, db: Session = Depends(get_db), current_user: Optional[AuthUser] = Depends(get_current_user)):
    """创建新的 LLM 配置"""
    user_id = current_user_id(current_user)
    cid = body.id
    if not cid:
        cid = f"llm_{uuid.uuid4().hex[:10]}"

    new_config = DBLLMConfig(
        id=cid,
        name=body.name,
        base_url=body.base_url,
        api_key=body.api_key,
        stream=body.stream,
        default_model=body.default_model,
        is_active=False,
        user_id=user_id,
    )

    db.add(new_config)
    db.commit()
    db.refresh(new_config)

    query = owner_only(db.query(DBLLMConfig), DBLLMConfig, user_id)
    total_count = query.count()
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
def update_config(config_id: str, body: LLMConfigIn, db: Session = Depends(get_db), current_user: Optional[AuthUser] = Depends(get_current_user)):
    """更新现有的 LLM 配置"""
    user_id = current_user_id(current_user)
    query = owner_only(
        db.query(DBLLMConfig).filter(DBLLMConfig.id == config_id),
        DBLLMConfig,
        user_id,
    )
    config = query.first()
    if not config:
        raise HTTPException(status_code=404, detail="config not found")

    config.name = body.name
    config.base_url = body.base_url
    config.api_key = body.api_key
    config.stream = body.stream
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
def delete_config(config_id: str, db: Session = Depends(get_db), current_user: Optional[AuthUser] = Depends(get_current_user)):
    """删除配置"""
    user_id = current_user_id(current_user)
    query = owner_only(
        db.query(DBLLMConfig).filter(DBLLMConfig.id == config_id),
        DBLLMConfig,
        user_id,
    )
    config = query.first()
    if not config:
        raise HTTPException(status_code=404, detail="config not found")

    was_active = config.is_active
    db.delete(config)
    db.commit()

    if was_active:
        fallback_query = owner_only(db.query(DBLLMConfig), DBLLMConfig, user_id)
        fallback = fallback_query.first()
        if fallback:
            fallback.is_active = True
            db.commit()

    return {"ok": True}


@router.put("/llm/active")
def set_active(body: ActiveLLM, db: Session = Depends(get_db), current_user: Optional[AuthUser] = Depends(get_current_user)):
    """设置当前激活的配置 ID 及选中的模型"""
    user_id = current_user_id(current_user)
    if not body.config_id:
        update_query = owner_only(db.query(DBLLMConfig), DBLLMConfig, user_id)
        update_query.update({DBLLMConfig.is_active: False})
        db.commit()
        return {}

    query = owner_only(
        db.query(DBLLMConfig).filter(DBLLMConfig.id == body.config_id),
        DBLLMConfig,
        user_id,
    )
    target = query.first()
    if not target:
        raise HTTPException(status_code=404, detail="config not found")

    update_query = owner_only(db.query(DBLLMConfig), DBLLMConfig, user_id)
    update_query.update({DBLLMConfig.is_active: False})

    target.is_active = True

    if body.model:
        target.default_model = body.model

    db.commit()
    db.refresh(target)

    return {
        "config_id": target.id,
        "model": target.default_model
    }


@router.get("/llm/configs/{config_id}/models")
def get_models_for_config(config_id: str, db: Session = Depends(get_db), current_user: Optional[AuthUser] = Depends(get_current_user)):
    """根据配置 ID 获取可用模型列表"""
    try:
        user_id = current_user_id(current_user)
        query = owner_only(
            db.query(DBLLMConfig).filter(DBLLMConfig.id == config_id),
            DBLLMConfig,
            user_id,
        )
        cfg = query.first()
        if not cfg:
            raise HTTPException(status_code=404, detail="配置不存在")

        # 验证配置数据
        if not cfg.base_url or not cfg.api_key:
            raise HTTPException(status_code=400, detail="配置信息不完整，请检查base_url和api_key")

        try:
            models = list_models(cfg.base_url, cfg.api_key)
        except LLMError as e:
            # 返回更详细的错误信息
            raise HTTPException(status_code=400, detail=f"获取模型列表失败: {str(e)}")

        return {"models": models}
        
    except HTTPException:
        # 重新抛出已知的HTTP异常
        raise
    except Exception as e:
        # 捕获所有其他异常，避免500错误
        logger.exception("get_models_for_config failed unexpectedly: %s", str(e))
        raise HTTPException(status_code=500, detail="服务器内部错误")


@router.post("/llm/models/list")
def list_models_by_credentials(body: ListModelsReq):
    """不保存配置，直接测试连接获取模型列表"""
    try:
        # 验证输入参数
        if not body.base_url or not body.base_url.strip():
            raise HTTPException(status_code=400, detail="base_url 不能为空")
        
        if not body.api_key or not body.api_key.strip():
            raise HTTPException(status_code=400, detail="api_key 不能为空")
        
        try:
            models = list_models(body.base_url, body.api_key)
        except LLMError as e:
            # 返回更详细的错误信息
            raise HTTPException(status_code=400, detail=f"获取模型列表失败: {str(e)}")
        
        return {"models": models}
        
    except HTTPException:
        # 重新抛出已知的HTTP异常
        raise
    except Exception as e:
        # 捕获所有其他异常，避免500错误
        logger.exception("list_models_by_credentials failed unexpectedly: %s", str(e))
        raise HTTPException(status_code=500, detail="服务器内部错误")
