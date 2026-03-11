from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session
from typing import Any, Dict, Optional
import json
from ..db.base import get_db
from ..db import models
from ..core.auth import get_current_user, User as AuthUser
from ..core.tenant import current_user_id, owner_only, owner_or_public, resolve_scoped_id

router = APIRouter(prefix="/api/templates", tags=["templates"])


@router.get("/list")
def list_templates(
    db: Session = Depends(get_db),
    current_user: Optional[AuthUser] = Depends(get_current_user)
):
    user_id = current_user_id(current_user)
    query = owner_or_public(db.query(models.CharacterTemplate), models.CharacterTemplate, user_id)

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
    user_id = current_user_id(current_user)
    requested_id = payload.get("id")
    if not requested_id:
        raise HTTPException(400, "Template ID is required")
    t_id = resolve_scoped_id(db, models.CharacterTemplate, "id", requested_id, user_id)

    new_t = models.CharacterTemplate(
        id=t_id,
        user_id=user_id,
        name=payload.get("name", "未命名"),
        description=payload.get("description", ""),
        config_json=json.dumps(payload.get("config", {}), ensure_ascii=False)
    )
    db.add(new_t)
    db.commit()
    return {"status": "ok", "id": t_id}


@router.put("/{template_id}")
def update_template(
    template_id: str,
    payload: Dict[str, Any] = Body(...),
    db: Session = Depends(get_db),
    current_user: Optional[AuthUser] = Depends(get_current_user)
):
    user_id = current_user_id(current_user)
    query = owner_only(
        db.query(models.CharacterTemplate).filter_by(id=template_id),
        models.CharacterTemplate,
        user_id,
    )
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
    user_id = current_user_id(current_user)
    query = owner_only(
        db.query(models.CharacterTemplate).filter_by(id=template_id),
        models.CharacterTemplate,
        user_id,
    )
    t = query.first()
    if not t:
        raise HTTPException(404, "Template not found or you don't have permission to delete it")

    # 系统级默认模板不允许删除
    if template_id == "system_default":
        raise HTTPException(400, "System default template cannot be deleted")

    db.delete(t)
    db.commit()
    return {"status": "deleted"}
