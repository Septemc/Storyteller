from typing import List, Optional, Any, Dict

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..db.base import get_db
from ..db import models

router = APIRouter()


class DungeonNodePayload(BaseModel):
    node_id: str
    name: str
    index: int = 0
    progress_percent: int = 0
    entry_conditions: List[Any] = []
    exit_conditions: List[Any] = []
    summary_requirements: str = ""
    story_requirements: Dict[str, Any] = {}
    branching: Dict[str, Any] = {}


class DungeonPayload(BaseModel):
    dungeon_id: str
    name: str
    description: str = ""
    level_min: int = 1
    level_max: int = 5
    global_rules: Dict[str, Any] = {}
    nodes: List[DungeonNodePayload] = []


class DungeonListItem(BaseModel):
    dungeon_id: str
    name: str
    level_min: Optional[int] = None
    level_max: Optional[int] = None


class DungeonListResponse(BaseModel):
    items: List[DungeonListItem]


@router.get("/dungeon/list", response_model=DungeonListResponse)
def list_dungeons(db: Session = Depends(get_db)) -> DungeonListResponse:
    rows = db.query(models.Dungeon).order_by(models.Dungeon.dungeon_id).all()
    items = [
        DungeonListItem(
            dungeon_id=d.dungeon_id,
            name=d.name,
            level_min=d.level_min,
            level_max=d.level_max,
        )
        for d in rows
    ]
    return DungeonListResponse(items=items)


@router.get("/dungeon/{dungeon_id}", response_model=DungeonPayload)
def get_dungeon(dungeon_id: str, db: Session = Depends(get_db)) -> DungeonPayload:
    import json

    d = (
        db.query(models.Dungeon)
        .filter(models.Dungeon.dungeon_id == dungeon_id)
        .first()
    )
    if not d:
        raise HTTPException(status_code=404, detail="副本不存在。")

    try:
        global_rules = json.loads(d.global_rules_json) if d.global_rules_json else {}
    except Exception:
        global_rules = {}

    nodes: List[DungeonNodePayload] = []
    for n in d.nodes:
        def parse_json_or(default: Any, value: Optional[str]) -> Any:
            if not value:
                return default
            import json as _json
            try:
                return _json.loads(value)
            except Exception:
                return default

        nodes.append(
            DungeonNodePayload(
                node_id=n.node_id,
                name=n.name,
                index=n.index_in_dungeon,
                progress_percent=n.progress_percent or 0,
                entry_conditions=parse_json_or([], n.entry_conditions_json),
                exit_conditions=parse_json_or([], n.exit_conditions_json),
                summary_requirements=n.summary_requirements or "",
                story_requirements=parse_json_or({}, n.story_requirements_json),
                branching=parse_json_or({}, n.branching_json),
            )
        )

    return DungeonPayload(
        dungeon_id=d.dungeon_id,
        name=d.name,
        description=d.description or "",
        level_min=d.level_min or 1,
        level_max=d.level_max or 5,
        global_rules=global_rules,
        nodes=nodes,
    )


@router.put("/dungeon/{dungeon_id}", response_model=DungeonPayload)
def upsert_dungeon(
    dungeon_id: str,
    payload: DungeonPayload,
    db: Session = Depends(get_db),
) -> DungeonPayload:
    import json

    d = (
        db.query(models.Dungeon)
        .filter(models.Dungeon.dungeon_id == dungeon_id)
        .first()
    )
    if not d:
        d = models.Dungeon(
            dungeon_id=dungeon_id,
            name=payload.name,
        )
        db.add(d)

    d.name = payload.name
    d.description = payload.description
    d.level_min = payload.level_min
    d.level_max = payload.level_max
    d.global_rules_json = json.dumps(payload.global_rules, ensure_ascii=False)

    d.nodes.clear()
    for node in payload.nodes:
        dn = models.DungeonNode(
            dungeon_id=dungeon_id,
            node_id=node.node_id,
            index_in_dungeon=node.index,
            name=node.name,
            progress_percent=node.progress_percent,
            entry_conditions_json=json.dumps(node.entry_conditions, ensure_ascii=False),
            exit_conditions_json=json.dumps(node.exit_conditions, ensure_ascii=False),
            summary_requirements=node.summary_requirements,
            story_requirements_json=json.dumps(node.story_requirements, ensure_ascii=False),
            branching_json=json.dumps(node.branching, ensure_ascii=False),
        )
        d.nodes.append(dn)

    db.commit()
    return payload
