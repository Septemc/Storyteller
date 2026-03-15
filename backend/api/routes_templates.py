from __future__ import annotations

import json
from typing import Any, Dict, Optional

from fastapi import APIRouter, Body, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from ..core.auth import User as AuthUser, get_current_user
from ..core.tenant import current_user_id, owner_only
from ..db import models
from ..db.base import get_db

router = APIRouter(prefix="/api/templates", tags=["templates"])


@router.get("/list")
def list_templates(
    session_id: str = Query(..., description="session id"),
    db: Session = Depends(get_db),
    current_user: Optional[AuthUser] = Depends(get_current_user),
):
    user_id = current_user_id(current_user)
    rows = owner_only(
        db.query(models.CharacterTemplate).filter(models.CharacterTemplate.session_id == session_id),
        models.CharacterTemplate,
        user_id,
    ).order_by(models.CharacterTemplate.updated_at.desc()).all()
    return {
        "items": [
            {
                "id": row.template_id,
                "session_id": row.session_id,
                "template_id": row.template_id,
                "name": row.template_name,
                "template_name": row.template_name,
                "config": json.loads(row.template_json or "{}"),
                "template_json": json.loads(row.template_json or "{}"),
                "is_active": row.is_active,
            }
            for row in rows
        ]
    }


@router.post("")
def create_template(
    payload: Dict[str, Any] = Body(...),
    db: Session = Depends(get_db),
    current_user: Optional[AuthUser] = Depends(get_current_user),
):
    user_id = current_user_id(current_user)
    session_id = str(payload.get("session_id") or "").strip()
    template_id = str(payload.get("id") or payload.get("template_id") or "").strip()
    if not session_id or not template_id:
        raise HTTPException(400, "session_id and template_id are required")
    if owner_only(db.query(models.CharacterTemplate).filter(models.CharacterTemplate.session_id == session_id, models.CharacterTemplate.template_id == template_id), models.CharacterTemplate, user_id).first():
        raise HTTPException(400, "template already exists")
    row = models.CharacterTemplate(
        user_id=user_id,
        session_id=session_id,
        template_id=template_id,
        template_name=payload.get("name") or payload.get("template_name") or template_id,
        template_json=json.dumps(payload.get("config") or payload.get("template_json") or {}, ensure_ascii=False),
        is_active=bool(payload.get("is_active")),
    )
    db.add(row)
    if row.is_active:
        owner_only(db.query(models.CharacterTemplate).filter(models.CharacterTemplate.session_id == session_id), models.CharacterTemplate, user_id).update({models.CharacterTemplate.is_active: False})
    db.commit()
    return {"status": "ok", "template_id": row.template_id}


@router.put("/{template_id}")
def update_template(
    template_id: str,
    payload: Dict[str, Any] = Body(...),
    db: Session = Depends(get_db),
    current_user: Optional[AuthUser] = Depends(get_current_user),
):
    user_id = current_user_id(current_user)
    session_id = str(payload.get("session_id") or "").strip()
    row = owner_only(db.query(models.CharacterTemplate).filter(models.CharacterTemplate.session_id == session_id, models.CharacterTemplate.template_id == template_id), models.CharacterTemplate, user_id).first()
    if not row:
        raise HTTPException(404, "Template not found")
    row.template_name = payload.get("name") or payload.get("template_name") or row.template_name
    if "config" in payload or "template_json" in payload:
        row.template_json = json.dumps(payload.get("config") or payload.get("template_json") or {}, ensure_ascii=False)
    if "is_active" in payload and payload.get("is_active"):
        _set_active_template(db, session_id, template_id, user_id)
        row.is_active = True
    db.commit()
    return {"status": "updated"}


@router.post("/{template_id}/activate")
def activate_template(
    template_id: str,
    session_id: str = Query(..., description="session id"),
    db: Session = Depends(get_db),
    current_user: Optional[AuthUser] = Depends(get_current_user),
):
    user_id = current_user_id(current_user)
    row = owner_only(db.query(models.CharacterTemplate).filter(models.CharacterTemplate.session_id == session_id, models.CharacterTemplate.template_id == template_id), models.CharacterTemplate, user_id).first()
    if not row:
        raise HTTPException(404, "Template not found")
    _set_active_template(db, session_id, template_id, user_id)
    db.commit()
    return {"status": "activated", "template_id": template_id}


@router.delete("/{template_id}")
def delete_template(
    template_id: str,
    session_id: str = Query(..., description="session id"),
    db: Session = Depends(get_db),
    current_user: Optional[AuthUser] = Depends(get_current_user),
):
    user_id = current_user_id(current_user)
    row = owner_only(db.query(models.CharacterTemplate).filter(models.CharacterTemplate.session_id == session_id, models.CharacterTemplate.template_id == template_id), models.CharacterTemplate, user_id).first()
    if not row:
        raise HTTPException(404, "Template not found")
    db.delete(row)
    db.commit()
    return {"status": "deleted"}


def _set_active_template(db: Session, session_id: str, template_id: str, user_id: Optional[str]) -> None:
    owner_only(db.query(models.CharacterTemplate).filter(models.CharacterTemplate.session_id == session_id), models.CharacterTemplate, user_id).update({models.CharacterTemplate.is_active: False})
    row = owner_only(db.query(models.CharacterTemplate).filter(models.CharacterTemplate.session_id == session_id, models.CharacterTemplate.template_id == template_id), models.CharacterTemplate, user_id).first()
    if row:
        row.is_active = True
