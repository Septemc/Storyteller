from __future__ import annotations

import json
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from ....core.auth import User as AuthUser, get_current_user
from ....core.tenant import current_user_id
from ....db import models
from ....db.base import get_db
from .helpers import apply_worldbook_filters, normalize_worldbook_id, semantic_match_score
from .schemas import WorldbookDetailResponse, WorldbookListItem, WorldbookListResponse, WorldbookSemanticSearchItem, WorldbookSemanticSearchRequest, WorldbookSemanticSearchResponse

router = APIRouter()


@router.get("/worldbook/list", response_model=WorldbookListResponse)
def list_worldbook(page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=2000), keyword: Optional[str] = Query(None), category: Optional[str] = Query(None), worldbook_id: Optional[str] = Query(None), db: Session = Depends(get_db), current_user: Optional[AuthUser] = Depends(get_current_user)) -> WorldbookListResponse:
    user_id = current_user_id(current_user)
    query = apply_worldbook_filters(db.query(models.WorldbookEntry), user_id, normalize_worldbook_id(worldbook_id))
    if keyword:
        like = f"%{keyword}%"
        query = query.filter((models.WorldbookEntry.title.like(like)) | (models.WorldbookEntry.content.like(like)) | (models.WorldbookEntry.tags.like(like)))
    if category:
        query = query.filter(models.WorldbookEntry.category == category)
    total = query.count()
    rows = query.order_by(models.WorldbookEntry.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
    items = []
    for row in rows:
        meta = json.loads(row.meta_json) if row.meta_json else {}
        items.append(WorldbookListItem(worldbook_id=row.worldbook_id, entry_id=row.entry_id, category=row.category, tags=row.tags.split(",") if row.tags else [], title=row.title, content=row.content, importance=row.importance, canonical=row.canonical, enabled=meta.get("enabled") if isinstance(meta, dict) else None, disable=meta.get("disable") if isinstance(meta, dict) else None, meta=meta if isinstance(meta, dict) else {}))
    return WorldbookListResponse(items=items, page=page, total_pages=max((total + page_size - 1) // page_size, 1))


@router.get("/worldbook/{entry_id}", response_model=WorldbookDetailResponse)
def get_worldbook_entry(entry_id: str, db: Session = Depends(get_db), current_user: Optional[AuthUser] = Depends(get_current_user)) -> WorldbookDetailResponse:
    entry = apply_worldbook_filters(db.query(models.WorldbookEntry).filter(models.WorldbookEntry.entry_id == entry_id), current_user_id(current_user)).first()
    if not entry:
        raise HTTPException(status_code=404, detail="worldbook entry not found")
    meta = json.loads(entry.meta_json) if entry.meta_json else {}
    return WorldbookDetailResponse(worldbook_id=entry.worldbook_id, entry_id=entry.entry_id, category=entry.category, tags=entry.tags.split(",") if entry.tags else [], title=entry.title, content=entry.content, importance=entry.importance, canonical=entry.canonical, meta=meta if isinstance(meta, dict) else {})


@router.post("/worldbook/semantic_search", response_model=WorldbookSemanticSearchResponse)
def semantic_search_worldbook(payload: WorldbookSemanticSearchRequest, db: Session = Depends(get_db), current_user: Optional[AuthUser] = Depends(get_current_user)) -> WorldbookSemanticSearchResponse:
    query = apply_worldbook_filters(db.query(models.WorldbookEntry), current_user_id(current_user), normalize_worldbook_id(payload.worldbook_id))
    if payload.category:
        query = query.filter(models.WorldbookEntry.category == payload.category)
    entries = query.all()
    if not entries or not payload.query.strip():
        return WorldbookSemanticSearchResponse(results=[])
    ranked = [WorldbookSemanticSearchItem(worldbook_id=entry.worldbook_id, entry_id=entry.entry_id, category=entry.category, title=entry.title, content=entry.content, importance=entry.importance, relevance_score=score) for entry in entries if (score := semantic_match_score(payload.query, entry)) > 0]
    ranked.sort(key=lambda item: item.relevance_score, reverse=True)
    return WorldbookSemanticSearchResponse(results=ranked[: max(payload.top_k, 1)])
