from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel


class DungeonNodePayload(BaseModel):
    node_id: str
    index_in_dungeon: int = 0
    name: str
    progress_percent: Optional[int] = None
    entry_conditions_json: Optional[str] = None
    exit_conditions_json: Optional[str] = None
    summary_requirements: Optional[str] = None
    story_requirements_json: Optional[str] = None
    branching_json: Optional[str] = None


class DungeonPayload(BaseModel):
    dungeon_id: str
    name: str
    description: Optional[str] = None
    level_min: Optional[int] = None
    level_max: Optional[int] = None
    global_rules_json: Optional[str] = None
    nodes: List[DungeonNodePayload] = []


class DungeonListItem(BaseModel):
    dungeon_id: str
    name: str


class DungeonListResponse(BaseModel):
    items: List[DungeonListItem]


class ScriptPayload(BaseModel):
    script_id: str
    name: str
    description: Optional[str] = None
    dungeon_ids_json: Optional[str] = "[]"
    meta_json: Optional[str] = None


class ScriptResponse(ScriptPayload):
    pass


class ScriptListItem(BaseModel):
    script_id: str
    name: str


class ScriptListResponse(BaseModel):
    items: List[ScriptListItem]
