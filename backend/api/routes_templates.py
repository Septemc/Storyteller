from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session
from typing import Any, Dict, Optional
import json
from ..db.base import get_db
from ..db import models
from ..core.auth import get_current_user, User as AuthUser

router = APIRouter(prefix="/api/templates", tags=["templates"])


@router.get("/list")
def list_templates(
    db: Session = Depends(get_db),
    current_user: Optional[AuthUser] = Depends(get_current_user)
):
    query = db.query(models.CharacterTemplate)
    
    # 如果用户已登录，只显示用户自己的模板和系统模板（user_id 为 NULL）
    if current_user:
        query = query.filter(
            (models.CharacterTemplate.user_id == current_user.user_id) |
            (models.CharacterTemplate.user_id == None)
        )
    else:
        # 未登录用户只能看到系统模板
        query = query.filter(models.CharacterTemplate.user_id == None)
    
    tmps = query.all()
    return {
        "items": [
            {
                "id": t.id,
                "name": t.name,
                "description": t.description,
                "config": json.loads(t.config_json)
            } for t in tmps
        ]
    }


@router.post("")
def create_template(
    payload: Dict[str, Any] = Body(...),
    db: Session = Depends(get_db),
    current_user: Optional[AuthUser] = Depends(get_current_user)
):
    t_id = payload.get("id")
    
    # 检查模板 ID 是否已存在
    existing_query = db.query(models.CharacterTemplate).filter_by(id=t_id)
    if current_user:
        # 如果用户已登录，检查是否是该用户的模板
        existing_query = existing_query.filter(
            (models.CharacterTemplate.user_id == current_user.user_id) |
            (models.CharacterTemplate.user_id == None)
        )
    
    if existing_query.first():
        raise HTTPException(400, "Template ID already exists")
    
    # 创建新模板
    new_t = models.CharacterTemplate(
        id=t_id,
        user_id=current_user.user_id if current_user else None,
        name=payload.get("name", "未命名"),
        description=payload.get("description", ""),
        config_json=json.dumps(payload.get("config", {}), ensure_ascii=False)
    )
    db.add(new_t)
    db.commit()
    return {"status": "ok"}


@router.put("/{template_id}")
def update_template(
    template_id: str,
    payload: Dict[str, Any] = Body(...),
    db: Session = Depends(get_db),
    current_user: Optional[AuthUser] = Depends(get_current_user)
):
    query = db.query(models.CharacterTemplate).filter_by(id=template_id)
    
    # 如果用户已登录，只能更新自己的模板
    if current_user:
        query = query.filter(models.CharacterTemplate.user_id == current_user.user_id)
    else:
        # 未登录用户不能更新模板
        raise HTTPException(401, "Authentication required")
    
    t = query.first()
    if not t:
        raise HTTPException(404, "Template not found or you don't have permission to update it")
    
    t.name = payload.get("name", t.name)
    t.description = payload.get("description", t.description)
    if "config" in payload:
        t.config_json = json.dumps(payload["config"], ensure_ascii=False)
    db.commit()
    return {"status": "updated"}


@router.delete("/{template_id}")
def delete_template(
    template_id: str,
    db: Session = Depends(get_db),
    current_user: Optional[AuthUser] = Depends(get_current_user)
):
    query = db.query(models.CharacterTemplate).filter_by(id=template_id)
    
    # 如果用户已登录，只能删除自己的模板
    if current_user:
        query = query.filter(models.CharacterTemplate.user_id == current_user.user_id)
    else:
        # 未登录用户不能删除模板
        raise HTTPException(401, "Authentication required")
    
    t = query.first()
    if not t:
        raise HTTPException(404, "Template not found or you don't have permission to delete it")

    # 系统级默认模板不允许删除
    if template_id == "system_default":
        raise HTTPException(400, "System default template cannot be deleted")

    db.delete(t)
    db.commit()
    return {"status": "deleted"}