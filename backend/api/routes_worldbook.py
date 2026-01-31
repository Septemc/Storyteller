from datetime import datetime
from typing import List, Optional, Any, Dict

from fastapi import APIRouter, Depends, HTTPException, Query, Body
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..db.base import get_db
from ..db import models

router = APIRouter()


class WorldbookListItem(BaseModel):
    entry_id: str
    category: Optional[str] = None
    title: str
    importance: Optional[float] = None


class WorldbookListResponse(BaseModel):
    items: List[WorldbookListItem]
    page: int
    total_pages: int


class WorldbookDetailResponse(BaseModel):
    entry_id: str
    category: Optional[str] = None
    tags: List[str] = []
    title: str
    content: str
    importance: Optional[float] = None
    canonical: Optional[bool] = None
    meta: Dict[str, Any] = {}


@router.post("/worldbook/import")
def import_worldbook(
    payload: Any = Body(..., description="世界书 JSON，可以是列表或带 entries 字段的对象"),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """
    最小导入实现：
    - 支持直接传入列表，每个元素是一条世界书记录
    - 或传入 {\"entries\": [...]} 这种结构
    - entry_id 如果未提供，会自动生成
    """
    import uuid
    import json

    if isinstance(payload, dict) and "entries" in payload:
        entries = payload["entries"]
    else:
        entries = payload

    if not isinstance(entries, list):
        raise HTTPException(status_code=400, detail="世界书导入格式错误：应为列表或包含 entries 的对象。")

    created = 0
    for raw in entries:
        if not isinstance(raw, dict):
            continue
        title = raw.get("title")
        content = raw.get("content")
        if not title or not content:
            continue

        entry_id = raw.get("entry_id") or f"WB_{uuid.uuid4().hex[:10]}"
        category = raw.get("category") or None
        tags = raw.get("tags") or []
        if isinstance(tags, list):
            tags_str = ",".join(str(t) for t in tags)
        else:
            tags_str = str(tags)

        meta = raw.get("meta") or {}
        meta_json = json.dumps(meta, ensure_ascii=False)

        existing = (
            db.query(models.WorldbookEntry)
            .filter(models.WorldbookEntry.entry_id == entry_id)
            .first()
        )
        if existing:
            existing.category = category
            existing.tags = tags_str
            existing.title = title
            existing.content = content
            existing.importance = float(raw.get("importance", existing.importance or 0.5))
            existing.canonical = bool(raw.get("canonical", existing.canonical or False))
            existing.meta_json = meta_json
            existing.updated_at = datetime.utcnow()
        else:
            entry = models.WorldbookEntry(
                entry_id=entry_id,
                category=category,
                tags=tags_str,
                title=title,
                content=content,
                importance=float(raw.get("importance", 0.5)),
                canonical=bool(raw.get("canonical", False)),
                meta_json=meta_json,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )
            db.add(entry)
        created += 1

    db.commit()
    return {"created_or_updated": created}


@router.get("/worldbook/list", response_model=WorldbookListResponse)
def list_worldbook(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    keyword: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    db: Session = Depends(get_db),
) -> WorldbookListResponse:
    query = db.query(models.WorldbookEntry)

    if keyword:
        like = f"%{keyword}%"
        query = query.filter(
            (models.WorldbookEntry.title.like(like))
            | (models.WorldbookEntry.content.like(like))
            | (models.WorldbookEntry.tags.like(like))
        )

    if category:
        query = query.filter(models.WorldbookEntry.category == category)

    total = query.count()
    total_pages = max((total + page_size - 1) // page_size, 1)

    items_db = (
        query.order_by(models.WorldbookEntry.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    items = [
        WorldbookListItem(
            entry_id=e.entry_id,
            category=e.category,
            title=e.title,
            importance=e.importance,
        )
        for e in items_db
    ]

    return WorldbookListResponse(items=items, page=page, total_pages=total_pages)


@router.get("/worldbook/{entry_id}", response_model=WorldbookDetailResponse)
def get_worldbook_entry(entry_id: str, db: Session = Depends(get_db)) -> WorldbookDetailResponse:
    import json

    e = (
        db.query(models.WorldbookEntry)
        .filter(models.WorldbookEntry.entry_id == entry_id)
        .first()
    )
    if not e:
        raise HTTPException(status_code=404, detail="世界书条目不存在。")

    tags = e.tags.split(",") if e.tags else []
    meta = {}
    if e.meta_json:
        try:
            meta = json.loads(e.meta_json)
        except Exception:
            meta = {}

    return WorldbookDetailResponse(
        entry_id=e.entry_id,
        category=e.category,
        tags=tags,
        title=e.title,
        content=e.content,
        importance=e.importance,
        canonical=e.canonical,
        meta=meta,
    )
