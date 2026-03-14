from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..db.base import get_db
from ..db import models
from ..core.auth import get_current_user, User as AuthUser
from ..core.tenant import current_user_id, owner_only

router = APIRouter()


class GlobalSettingsPayload(BaseModel):
    """
    直接承载前端发来的配置 JSON。
    内部不做字段拆分，全部存为一条 JSON。
    """
    ui: Dict[str, Any] = {}
    text: Dict[str, Any] = {}
    summary: Dict[str, Any] = {}
    variables: Dict[str, Any] = {}
    text_opt: Dict[str, Any] = {}
    world_evolution: Dict[str, Any] = {}
    default_profiles: Dict[str, Any] = {}
    worldbook: Dict[str, Any] = {}


def _settings_key(user_id: Optional[str]) -> str:
    if user_id:
        return f"global::{user_id}"
    return "global::public"


@router.get("/settings/global", response_model=GlobalSettingsPayload)
def get_global_settings(db: Session = Depends(get_db), current_user: Optional[AuthUser] = Depends(get_current_user)) -> GlobalSettingsPayload:
    user_id = current_user_id(current_user)
    key = _settings_key(user_id)

    row = owner_only(
        db.query(models.GlobalSetting).filter(models.GlobalSetting.key == key),
        models.GlobalSetting,
        user_id,
    ).first()

    if not row:
        legacy = owner_only(
            db.query(models.GlobalSetting).filter(models.GlobalSetting.key == "global"),
            models.GlobalSetting,
            user_id,
        ).first()
        if legacy:
            legacy.key = key
            db.commit()
            row = legacy
    
    import json

    if not row:
        default = GlobalSettingsPayload()
        return default

    try:
        data = json.loads(row.value_json)
    except Exception:
        data = {}

    return GlobalSettingsPayload(**data)


@router.put("/settings/global", response_model=GlobalSettingsPayload)
def put_global_settings(
    payload: GlobalSettingsPayload,
    db: Session = Depends(get_db),
    current_user: Optional[AuthUser] = Depends(get_current_user),
) -> GlobalSettingsPayload:
    import json
    user_id = current_user_id(current_user)
    key = _settings_key(user_id)

    row = owner_only(
        db.query(models.GlobalSetting).filter(models.GlobalSetting.key == key),
        models.GlobalSetting,
        user_id,
    ).first()
    
    if not row:
        row = models.GlobalSetting(
            key=key,
            value_json=json.dumps(payload.dict(), ensure_ascii=False),
            user_id=user_id,
        )
        db.add(row)
    else:
        row.value_json = json.dumps(payload.dict(), ensure_ascii=False)

    db.commit()
    return payload
