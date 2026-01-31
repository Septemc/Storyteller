from typing import Any, Dict

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..db.base import get_db
from ..db import models

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


@router.get("/settings/global", response_model=GlobalSettingsPayload)
def get_global_settings(db: Session = Depends(get_db)) -> GlobalSettingsPayload:
    row = (
        db.query(models.GlobalSetting)
        .filter(models.GlobalSetting.key == "global")
        .first()
    )
    import json

    if not row:
        # 初次启动时给一个默认配置
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
) -> GlobalSettingsPayload:
    import json

    row = (
        db.query(models.GlobalSetting)
        .filter(models.GlobalSetting.key == "global")
        .first()
    )
    if not row:
        row = models.GlobalSetting(
            key="global",
            value_json=json.dumps(payload.dict(), ensure_ascii=False),
        )
        db.add(row)
    else:
        row.value_json = json.dumps(payload.dict(), ensure_ascii=False)

    db.commit()
    return payload
