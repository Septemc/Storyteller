from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ....core.auth import User as AuthUser, get_current_user
from ....core.tenant import current_user_id, owner_only
from ....db import models
from ....db.base import get_db
from .schemas import DungeonListItem, DungeonListResponse, DungeonPayload, ScriptListItem, ScriptListResponse, ScriptPayload, ScriptResponse

router = APIRouter()


@router.get("/dungeon/list", response_model=DungeonListResponse)
def list_dungeons(db: Session = Depends(get_db), current_user: Optional[AuthUser] = Depends(get_current_user)) -> DungeonListResponse:
    rows = owner_only(db.query(models.Dungeon), models.Dungeon, current_user_id(current_user)).all()
    return DungeonListResponse(items=[DungeonListItem(dungeon_id=row.dungeon_id, name=row.name) for row in rows])


@router.get("/dungeon/{dungeon_id}", response_model=DungeonPayload)
def get_dungeon(dungeon_id: str, db: Session = Depends(get_db), current_user: Optional[AuthUser] = Depends(get_current_user)) -> DungeonPayload:
    row = owner_only(db.query(models.Dungeon).filter(models.Dungeon.dungeon_id == dungeon_id), models.Dungeon, current_user_id(current_user)).first()
    if not row:
        raise HTTPException(status_code=404, detail="dungeon not found")
    return DungeonPayload(dungeon_id=row.dungeon_id, name=row.name, description=row.description, level_min=row.level_min, level_max=row.level_max, global_rules_json=row.global_rules_json, nodes=[node for node in row.nodes])


@router.put("/dungeon/{dungeon_id}", response_model=DungeonPayload)
def upsert_dungeon(dungeon_id: str, body: DungeonPayload, db: Session = Depends(get_db), current_user: Optional[AuthUser] = Depends(get_current_user)):
    user_id = current_user_id(current_user)
    row = owner_only(db.query(models.Dungeon).filter(models.Dungeon.dungeon_id == dungeon_id), models.Dungeon, user_id).first() or models.Dungeon(dungeon_id=dungeon_id, user_id=user_id)
    if row.id is None:
        db.add(row)
    row.name, row.description, row.level_min, row.level_max, row.global_rules_json = body.name, body.description, body.level_min, body.level_max, body.global_rules_json
    existing_nodes = {node.node_id: node for node in row.nodes}
    row.nodes[:] = []
    for node_payload in body.nodes:
        node = existing_nodes.get(node_payload.node_id) or models.DungeonNode(dungeon_id=dungeon_id, node_id=node_payload.node_id)
        for field, value in node_payload.model_dump().items():
            setattr(node, field, value)
        row.nodes.append(node)
    db.commit()
    db.refresh(row)
    return DungeonPayload(**body.model_dump())


@router.delete("/dungeon/{dungeon_id}")
def delete_dungeon(dungeon_id: str, db: Session = Depends(get_db), current_user: Optional[AuthUser] = Depends(get_current_user)):
    row = owner_only(db.query(models.Dungeon).filter(models.Dungeon.dungeon_id == dungeon_id), models.Dungeon, current_user_id(current_user)).first()
    if not row:
        raise HTTPException(status_code=404, detail="dungeon not found")
    db.delete(row)
    db.commit()
    return {"ok": True}


@router.get("/scripts", response_model=ScriptListResponse)
def list_scripts(db: Session = Depends(get_db), current_user: Optional[AuthUser] = Depends(get_current_user)) -> ScriptListResponse:
    rows = owner_only(db.query(models.Script), models.Script, current_user_id(current_user)).all()
    return ScriptListResponse(items=[ScriptListItem(script_id=row.script_id, name=row.name) for row in rows])


@router.get("/scripts/{script_id}", response_model=ScriptResponse)
def get_script(script_id: str, db: Session = Depends(get_db), current_user: Optional[AuthUser] = Depends(get_current_user)) -> ScriptResponse:
    row = owner_only(db.query(models.Script).filter(models.Script.script_id == script_id), models.Script, current_user_id(current_user)).first()
    if not row:
        raise HTTPException(status_code=404, detail="script not found")
    return ScriptResponse(script_id=row.script_id, name=row.name, description=row.description, dungeon_ids_json=row.dungeon_ids_json, meta_json=row.meta_json)


@router.put("/scripts/{script_id}", response_model=ScriptResponse)
def upsert_script(script_id: str, body: ScriptPayload, db: Session = Depends(get_db), current_user: Optional[AuthUser] = Depends(get_current_user)):
    user_id = current_user_id(current_user)
    row = owner_only(db.query(models.Script).filter(models.Script.script_id == script_id), models.Script, user_id).first() or models.Script(script_id=script_id, user_id=user_id)
    if row.id is None:
        db.add(row)
    row.name, row.description, row.dungeon_ids_json, row.meta_json = body.name, body.description, body.dungeon_ids_json, body.meta_json
    db.commit()
    db.refresh(row)
    return ScriptResponse(script_id=row.script_id, name=row.name, description=row.description, dungeon_ids_json=row.dungeon_ids_json, meta_json=row.meta_json)


@router.delete("/scripts/{script_id}")
def delete_script(script_id: str, db: Session = Depends(get_db), current_user: Optional[AuthUser] = Depends(get_current_user)):
    row = owner_only(db.query(models.Script).filter(models.Script.script_id == script_id), models.Script, current_user_id(current_user)).first()
    if not row:
        raise HTTPException(status_code=404, detail="script not found")
    db.delete(row)
    db.commit()
    return {"ok": True}
