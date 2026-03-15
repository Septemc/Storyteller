from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel


class CharacterListItem(BaseModel):
    session_id: str
    character_id: str
    display_name: str
    developer_name: Optional[str] = None
    type: str
    status: str
    source_type: str
    template_id: Optional[str] = None
    story_id: Optional[str] = None
    ability_tier: Optional[str] = None


class CharacterListResponse(BaseModel):
    items: List[CharacterListItem]


class CharacterDetailResponse(BaseModel):
    session_id: str
    character_id: str
    template_id: Optional[str] = None
    type: str
    display_name: str
    developer_name: Optional[str] = None
    source_type: str
    status: str
    story_id: Optional[str] = None
    template: Optional[Dict[str, Any]] = None
    full_profile: Dict[str, Any] = {}
    player_profile: Dict[str, Any] = {}
    meta: Dict[str, Any] = {}
