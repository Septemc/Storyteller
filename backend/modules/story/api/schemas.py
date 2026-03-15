from __future__ import annotations

from typing import Dict, List, Optional

from pydantic import BaseModel


class StoryGenerateRequest(BaseModel):
    session_id: str
    user_input: str
    frontend_duration: Optional[float] = None
    reasoning_strength: Optional[str] = "low"


class StoryMeta(BaseModel):
    scene_title: str = ""
    tags: List[str] = []
    tone: Optional[str] = None
    pacing: Optional[str] = None
    dungeon_progress_hint: Optional[str] = None
    dungeon_name: Optional[str] = None
    dungeon_node_name: Optional[str] = None
    main_character: Optional[Dict] = None
    word_count: Optional[int] = None
    duration_ms: Optional[int] = None


class StoryGenerateResponse(BaseModel):
    story: str
    meta: StoryMeta
    segment_id: Optional[str] = None
    dev_log_info: Optional[Dict] = None


class SessionSummaryDungeon(BaseModel):
    name: Optional[str] = None
    current_node_name: Optional[str] = None
    progress_hint: Optional[str] = None


class SessionSummaryCharacter(BaseModel):
    character_id: str
    name: Optional[str] = None
    ability_tier: Optional[str] = None


class SessionSummaryVariables(BaseModel):
    main_character: Optional[Dict] = None
    faction_summary: Optional[str] = None


class SessionSummaryResponse(BaseModel):
    dungeon: Optional[SessionSummaryDungeon] = None
    characters: List[SessionSummaryCharacter] = []
    variables: Optional[SessionSummaryVariables] = None


class SessionContextUpdateRequest(BaseModel):
    session_id: str
    main_character_id: Optional[str] = None
    current_script_id: Optional[str] = None
    current_dungeon_id: Optional[str] = None
    current_node_id: Optional[str] = None
    active_preset_id: Optional[str] = None
    active_llm_config_id: Optional[str] = None
    active_model: Optional[str] = None
    reasoning_strength: Optional[str] = None


class StorySegmentItem(BaseModel):
    segment_id: str
    order_index: int
    user_input: Optional[str] = None
    text: str
    agent_public_log: Optional[Dict] = None
    agent_dev_log: Optional[Dict] = None
    paragraph_word_count: int = 0
    cumulative_word_count: int = 0
    frontend_duration: float = 0.0
    backend_duration: float = 0.0
    created_at: Optional[str] = None


class RecentSegmentsResponse(BaseModel):
    segments: List[StorySegmentItem]


class UpdateFrontendDurationRequest(BaseModel):
    segment_id: str
    frontend_duration: float


class UpdateSegmentRequest(BaseModel):
    segment_id: str
    text: str


class SaveInfo(BaseModel):
    session_id: str
    display_name: str
    segment_count: int
    total_word_count: int
    story_id: Optional[str] = None
    story_title: Optional[str] = None
    branch_id: Optional[str] = None
    branch_display_name: Optional[str] = None
    branch_type: Optional[str] = None
    branch_status: Optional[str] = None
    parent_branch_id: Optional[str] = None
    reasoning_strength: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class BranchInfo(BaseModel):
    branch_id: str
    session_id: str
    display_name: str
    branch_type: Optional[str] = None
    status: Optional[str] = None
    parent_branch_id: Optional[str] = None
    last_segment_id: Optional[str] = None
    reasoning_strength: Optional[str] = None
    segment_count: int = 0
    total_word_count: int = 0
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class SaveDetail(BaseModel):
    session_id: str
    display_name: str
    segment_count: int
    total_word_count: int
    story_id: Optional[str] = None
    story_title: Optional[str] = None
    branch_id: Optional[str] = None
    branch_display_name: Optional[str] = None
    branch_type: Optional[str] = None
    branch_status: Optional[str] = None
    parent_branch_id: Optional[str] = None
    reasoning_strength: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    story_branch_count: int = 0
    branches: List[BranchInfo] = []
    segments: List[dict] = []


class SaveRenameRequest(BaseModel):
    session_id: str
    display_name: str


class StoryRenameRequest(BaseModel):
    story_id: str
    title: str


class BranchRenameRequest(BaseModel):
    session_id: str
    display_name: str


class CreateBranchRequest(BaseModel):
    source_session_id: str


class DeleteSegmentCascadeRequest(BaseModel):
    session_id: str
    from_order_index: int


class CopySaveFromSegmentRequest(BaseModel):
    source_session_id: str
    to_order_index: int
