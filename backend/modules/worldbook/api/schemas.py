from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class WorldbookListItem(BaseModel):
    worldbook_id: str
    entry_id: str
    category: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    title: str
    content: Optional[str] = None
    importance: Optional[float] = None
    canonical: Optional[bool] = None
    enabled: Optional[bool] = None
    disable: Optional[bool] = None
    meta: Dict[str, Any] = Field(default_factory=dict)


class WorldbookListResponse(BaseModel):
    items: List[WorldbookListItem]
    page: int
    total_pages: int


class WorldbookDetailResponse(BaseModel):
    worldbook_id: str
    entry_id: str
    category: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    title: str
    content: str
    importance: Optional[float] = None
    canonical: Optional[bool] = None
    meta: Dict[str, Any] = Field(default_factory=dict)


class WorldbookSemanticSearchRequest(BaseModel):
    query: str
    top_k: int = 20
    use_hybrid: bool = True
    category: Optional[str] = None
    worldbook_id: Optional[str] = None


class WorldbookSemanticSearchItem(BaseModel):
    worldbook_id: str
    entry_id: str
    category: Optional[str] = None
    title: str
    content: str
    importance: Optional[float] = None
    relevance_score: float


class WorldbookSemanticSearchResponse(BaseModel):
    results: List[WorldbookSemanticSearchItem]
