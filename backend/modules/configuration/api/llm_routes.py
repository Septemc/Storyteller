from __future__ import annotations

import logging
import uuid
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ....core.auth import User as AuthUser, get_current_user
from ....core.llm_client import LLMError, list_models
from ....core.tenant import current_user_id, owner_only, owner_or_public
from ....db.base import get_db
from ....db.models import DBLLMConfig
from .llm_schemas import ActiveLLM, LLMConfigIn, LLMConfigOut, ListModelsReq

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get('/llm/configs')
def get_configs(db: Session = Depends(get_db), current_user: Optional[AuthUser] = Depends(get_current_user)) -> Dict[str, Any]:
    if not current_user:
        raise HTTPException(status_code=401, detail='需要登录后才能访问 LLM 配置')
    user_id = current_user_id(current_user)
    rows = sorted(owner_or_public(db.query(DBLLMConfig), DBLLMConfig, user_id).all(), key=lambda row: (getattr(row, 'user_id', None) != user_id, row.name or row.id))
    active_rows = owner_or_public(db.query(DBLLMConfig).filter(DBLLMConfig.is_active == True), DBLLMConfig, user_id).all()
    active_row = next((item for item in active_rows if getattr(item, 'user_id', None) == user_id), None) or next((item for item in active_rows if getattr(item, 'user_id', None) is None), None)
    configs = [{'id': row.id, 'name': row.name, 'base_url': row.base_url, 'api_key': row.api_key, 'stream': row.stream, 'default_model': row.default_model} for row in rows]
    return {'configs': configs, 'active': {'config_id': active_row.id, 'model': active_row.default_model} if active_row else {}}


@router.post('/llm/configs', response_model=LLMConfigOut)
def create_config(body: LLMConfigIn, db: Session = Depends(get_db), current_user: Optional[AuthUser] = Depends(get_current_user)):
    user_id = current_user_id(current_user)
    new_config = DBLLMConfig(id=body.id or f'llm_{uuid.uuid4().hex[:10]}', name=body.name, base_url=body.base_url, api_key=body.api_key, stream=body.stream, default_model=body.default_model, is_active=False, user_id=user_id)
    db.add(new_config)
    db.commit()
    if owner_only(db.query(DBLLMConfig), DBLLMConfig, user_id).count() == 1:
        new_config.is_active = True
        db.commit()
    db.refresh(new_config)
    return _to_config_out(new_config)


@router.put('/llm/configs/{config_id}', response_model=LLMConfigOut)
def update_config(config_id: str, body: LLMConfigIn, db: Session = Depends(get_db), current_user: Optional[AuthUser] = Depends(get_current_user)):
    config = _owned_config_or_404(db, config_id, current_user_id(current_user))
    config.name = body.name
    config.base_url = body.base_url
    config.api_key = body.api_key
    config.stream = body.stream
    config.default_model = body.default_model
    db.commit()
    db.refresh(config)
    return _to_config_out(config)


@router.delete('/llm/configs/{config_id}')
def delete_config(config_id: str, db: Session = Depends(get_db), current_user: Optional[AuthUser] = Depends(get_current_user)):
    user_id = current_user_id(current_user)
    config = _owned_config_or_404(db, config_id, user_id)
    was_active = config.is_active
    db.delete(config)
    db.commit()
    if was_active:
        fallback = owner_only(db.query(DBLLMConfig), DBLLMConfig, user_id).first()
        if fallback:
            fallback.is_active = True
            db.commit()
    return {'ok': True}


@router.put('/llm/active')
def set_active(body: ActiveLLM, db: Session = Depends(get_db), current_user: Optional[AuthUser] = Depends(get_current_user)):
    user_id = current_user_id(current_user)
    if not body.config_id:
        owner_only(db.query(DBLLMConfig), DBLLMConfig, user_id).update({DBLLMConfig.is_active: False})
        db.commit()
        return {}
    target = _owned_config_or_404(db, body.config_id, user_id)
    owner_only(db.query(DBLLMConfig), DBLLMConfig, user_id).update({DBLLMConfig.is_active: False})
    target.is_active = True
    if body.model:
        target.default_model = body.model
    db.commit()
    db.refresh(target)
    return {'config_id': target.id, 'model': target.default_model}


@router.get('/llm/configs/{config_id}/models')
def get_models_for_config(config_id: str, db: Session = Depends(get_db), current_user: Optional[AuthUser] = Depends(get_current_user)):
    try:
        cfg = _owned_config_or_404(db, config_id, current_user_id(current_user))
        if not cfg.base_url or not cfg.api_key:
            raise HTTPException(status_code=400, detail='配置不完整，请检查 Base URL 和 API Key')
        return {'models': list_models(cfg.base_url, cfg.api_key)}
    except LLMError as exc:
        raise HTTPException(status_code=400, detail=f'获取模型列表失败: {exc}') from exc
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception('get_models_for_config failed unexpectedly: %s', str(exc))
        raise HTTPException(status_code=500, detail='服务器内部错误') from exc


@router.post('/llm/models/list')
def list_models_by_credentials(body: ListModelsReq):
    if not body.base_url.strip():
        raise HTTPException(status_code=400, detail='base_url 不能为空')
    if not body.api_key.strip():
        raise HTTPException(status_code=400, detail='api_key 不能为空')
    try:
        return {'models': list_models(body.base_url, body.api_key)}
    except LLMError as exc:
        raise HTTPException(status_code=400, detail=f'获取模型列表失败: {exc}') from exc
    except Exception as exc:
        logger.exception('list_models_by_credentials failed unexpectedly: %s', str(exc))
        raise HTTPException(status_code=500, detail='服务器内部错误') from exc


def _owned_config_or_404(db: Session, config_id: str, user_id: Optional[str]) -> DBLLMConfig:
    config = owner_only(db.query(DBLLMConfig).filter(DBLLMConfig.id == config_id), DBLLMConfig, user_id).first()
    if not config:
        raise HTTPException(status_code=404, detail='config not found')
    return config


def _to_config_out(config: DBLLMConfig) -> LLMConfigOut:
    return LLMConfigOut(id=config.id, name=config.name, base_url=config.base_url, api_key=config.api_key, stream=config.stream, default_model=config.default_model)
