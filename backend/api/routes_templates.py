from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session
from typing import Any, Dict
import json
from ..db.base import get_db
from ..db import models

router = APIRouter(prefix="/api/templates", tags=["templates"])


@router.get("/list")
def list_templates(db: Session = Depends(get_db)):
    tmps = db.query(models.CharacterTemplate).all()
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
def create_template(payload: Dict[str, Any] = Body(...), db: Session = Depends(get_db)):
    t_id = payload.get("id")
    if db.query(models.CharacterTemplate).filter_by(id=t_id).first():
        raise HTTPException(400, "Template ID already exists")
    new_t = models.CharacterTemplate(
        id=t_id,
        name=payload.get("name", "未命名"),
        config_json=json.dumps(payload.get("config", {}), ensure_ascii=False)
    )
    db.add(new_t)
    db.commit()
    return {"status": "ok"}


@router.put("/{template_id}")
def update_template(template_id: str, payload: Dict[str, Any] = Body(...), db: Session = Depends(get_db)):
    t = db.query(models.CharacterTemplate).filter_by(id=template_id).first()
    if not t: raise HTTPException(404, "Template not found")
    t.name = payload.get("name", t.name)
    if "config" in payload:
        t.config_json = json.dumps(payload["config"], ensure_ascii=False)
    db.commit()
    return {"status": "updated"}


# 新增：删除模板接口 (需求 5)
@router.delete("/{template_id}")
def delete_template(template_id: str, db: Session = Depends(get_db)):
    t = db.query(models.CharacterTemplate).filter_by(id=template_id).first()
    if not t:
        raise HTTPException(404, "Template not found")

    # 注意：系统级默认模板通常不允许删除，可在业务层做判断
    if template_id == "system_default":
        raise HTTPException(400, "System default template cannot be deleted")

    db.delete(t)
    db.commit()
    return {"status": "deleted"}