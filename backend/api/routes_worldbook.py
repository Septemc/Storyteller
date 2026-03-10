from datetime import datetime
from typing import List, Optional, Any, Dict

from fastapi import APIRouter, Depends, HTTPException, Query, Body, BackgroundTasks
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..db.base import get_db, SessionLocal
from ..db import models
from ..core.auth import get_current_user, User as AuthUser

router = APIRouter()


class WorldbookListItem(BaseModel):
    entry_id: str
    category: Optional[str] = None
    title: str
    content: Optional[str] = None
    importance: Optional[float] = None
    enabled: Optional[bool] = None
    disable: Optional[bool] = None
    meta: Dict[str, Any] = {}


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
    background_tasks: BackgroundTasks = None,
    sync_embeddings: bool = Query(False, description="是否同步计算向量（默认异步）"),
    current_user: Optional[AuthUser] = Depends(get_current_user),
) -> Dict[str, Any]:
    """
    最小导入实现：
    - 支持直接传入列表，每个元素是一条世界书记录
    - 或传入 {"entries": [...]} 这种结构
    - entry_id 如果未提供，会自动生成
    - 自动计算并保存向量缓存
    """
    import uuid
    import json
    user_id = current_user.user_id if current_user else None

    if isinstance(payload, dict) and "entries" in payload:
        entries = payload["entries"]
    else:
        entries = payload

    if not isinstance(entries, list):
        raise HTTPException(status_code=400, detail="世界书导入格式错误：应为列表或包含 entries 的对象。")

    created = 0
    updated = 0
    entries_to_embed = []
    
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
        if not isinstance(meta, dict):
            meta = {}
        # 保留条目层级的开关字段
        if "enabled" not in meta and "enabled" in raw:
            meta["enabled"] = raw.get("enabled")
        if "disable" not in meta and "disable" in raw:
            meta["disable"] = raw.get("disable")
        if "disabled" in raw and "disable" not in meta:
            meta["disable"] = raw.get("disabled")
        meta_json = json.dumps(meta, ensure_ascii=False)

        existing_query = db.query(models.WorldbookEntry).filter(
            models.WorldbookEntry.entry_id == entry_id
        )
        if user_id:
            existing_query = existing_query.filter(models.WorldbookEntry.user_id == user_id)
        existing = existing_query.first()
        
        if existing:
            existing.category = category
            existing.tags = tags_str
            existing.title = title
            existing.content = content
            existing.importance = float(raw.get("importance", existing.importance or 0.5))
            existing.canonical = bool(raw.get("canonical", existing.canonical or False))
            existing.meta_json = meta_json
            existing.updated_at = datetime.utcnow()
            entries_to_embed.append(existing)
            updated += 1
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
                user_id=user_id,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )
            db.add(entry)
            entries_to_embed.append(entry)
            created += 1

    db.commit()
    
    # 计算并保存向量缓存（可选同步 / 默认异步）
    entry_ids = [e.entry_id for e in entries_to_embed]

    def _compute_embeddings(entry_ids_local: List[str]) -> None:
        if not entry_ids_local:
            return
        db2 = SessionLocal()
        try:
            from ..core.rag import create_retriever
            retriever = create_retriever(db2)
            for eid in entry_ids_local:
                try:
                    entry = db2.query(models.WorldbookEntry).filter(models.WorldbookEntry.entry_id == eid).first()
                    if entry:
                        retriever.compute_entry_embedding(entry, use_cache=False)
                except Exception as e:
                    print(f"[导入] 计算向量失败 {eid}: {e}")
        except Exception as e:
            print(f"[导入] 向量计算失败：{e}")
        finally:
            db2.close()

    if entry_ids:
        if sync_embeddings:
            _compute_embeddings(entry_ids)
        else:
            if background_tasks is not None:
                background_tasks.add_task(_compute_embeddings, entry_ids)
            else:
                # 兜底：没有 BackgroundTasks 时同步执行
                _compute_embeddings(entry_ids)
    
    return {"created_or_updated": created + updated, "created": created, "updated": updated, "embeddings": "queued" if (entry_ids and not sync_embeddings) else "done"}


@router.get("/worldbook/list", response_model=WorldbookListResponse)
def list_worldbook(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    keyword: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: Optional[AuthUser] = Depends(get_current_user),
) -> WorldbookListResponse:
    # 未登录时，允许访问 user_id 为 NULL 的公共世界书
    user_id = current_user.user_id if current_user else None
    query = db.query(models.WorldbookEntry)
    if user_id:
        # 登录用户：同时看到个人条目与公共条目
        query = query.filter(
            (models.WorldbookEntry.user_id == user_id) |
            (models.WorldbookEntry.user_id == None)
        )
    else:
        # 未登录：仅公共条目
        query = query.filter(models.WorldbookEntry.user_id == None)

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

    import json as _json
    items: List[WorldbookListItem] = []
    for e in items_db:
        meta = {}
        if e.meta_json:
            try:
                meta = _json.loads(e.meta_json)
            except Exception:
                meta = {}
        enabled = meta.get("enabled") if isinstance(meta, dict) else None
        disable = meta.get("disable") if isinstance(meta, dict) else None
        items.append(
            WorldbookListItem(
                entry_id=e.entry_id,
                category=e.category,
                title=e.title,
                content=e.content,
                importance=e.importance,
                enabled=enabled,
                disable=disable,
                meta=meta if isinstance(meta, dict) else {},
            )
        )

    return WorldbookListResponse(items=items, page=page, total_pages=total_pages)


@router.get("/worldbook/{entry_id}", response_model=WorldbookDetailResponse)
def get_worldbook_entry(entry_id: str, db: Session = Depends(get_db), current_user: Optional[AuthUser] = Depends(get_current_user)) -> WorldbookDetailResponse:
    import json
    user_id = current_user.user_id if current_user else None
    query = db.query(models.WorldbookEntry).filter(
        models.WorldbookEntry.entry_id == entry_id
    )
    if user_id:
        query = query.filter(
            (models.WorldbookEntry.user_id == user_id) |
            (models.WorldbookEntry.user_id == None)
        )
    else:
        query = query.filter(models.WorldbookEntry.user_id == None)
    e = query.first()
    
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


@router.delete("/worldbook/category")
def delete_worldbook_category(
    category: str = Query(..., description="要删除的分类名称"),
    db: Session = Depends(get_db),
    current_user: Optional[AuthUser] = Depends(get_current_user),
) -> Dict[str, Any]:
    user_id = current_user.user_id if current_user else None
    query = db.query(models.WorldbookEntry).filter(
        models.WorldbookEntry.category == category
    )
    if user_id:
        query = query.filter(
            (models.WorldbookEntry.user_id == user_id) |
            (models.WorldbookEntry.user_id == None)
        )
    else:
        query = query.filter(models.WorldbookEntry.user_id == None)
    entries = query.all()
    
    if not entries:
        return {"success": True, "deleted": 0}
    
    entry_ids = [e.entry_id for e in entries]
    
    # 删除向量缓存
    db.query(models.WorldbookEmbedding).filter(
        models.WorldbookEmbedding.entry_id.in_(entry_ids)
    ).delete(synchronize_session=False)
    
    deleted_count = query.delete(synchronize_session=False)
    db.commit()
    
    return {"success": True, "deleted": deleted_count}


@router.delete("/worldbook/all")
def delete_all_worldbook_entries(
    confirm: bool = Query(False, description="确认删除全部条目"),
    db: Session = Depends(get_db),
    current_user: Optional[AuthUser] = Depends(get_current_user),
) -> Dict[str, Any]:
    if not confirm:
        raise HTTPException(status_code=400, detail="需要确认删除全部条目（confirm=true）")

    user_id = current_user.user_id if current_user else None
    entries_query = db.query(models.WorldbookEntry)
    if user_id:
        entries_query = entries_query.filter(
            (models.WorldbookEntry.user_id == user_id) |
            (models.WorldbookEntry.user_id == None)
        )
    else:
        entries_query = entries_query.filter(models.WorldbookEntry.user_id == None)

    entries = entries_query.all()
    
    if not entries:
        return {"success": True, "deleted": 0}
    
    entry_ids = [e.entry_id for e in entries]
    
    # 删除向量缓存
    db.query(models.WorldbookEmbedding).filter(
        models.WorldbookEmbedding.entry_id.in_(entry_ids)
    ).delete(synchronize_session=False)
    
    deleted_count = entries_query.delete(synchronize_session=False)
    
    db.commit()
    
    return {"success": True, "deleted": deleted_count}


@router.delete("/worldbook/{entry_id}")
def delete_worldbook_entry(
    entry_id: str,
    db: Session = Depends(get_db),
    current_user: Optional[AuthUser] = Depends(get_current_user),
) -> Dict[str, Any]:
    user_id = current_user.user_id if current_user else None
    query = db.query(models.WorldbookEntry).filter(
        models.WorldbookEntry.entry_id == entry_id
    )
    if user_id:
        query = query.filter(
            (models.WorldbookEntry.user_id == user_id) |
            (models.WorldbookEntry.user_id == None)
        )
    else:
        query = query.filter(models.WorldbookEntry.user_id == None)
    entry = query.first()
    
    if not entry:
        raise HTTPException(status_code=404, detail="世界书条目不存在。")
    
    # 同步删除向量缓存
    db.query(models.WorldbookEmbedding).filter(
        models.WorldbookEmbedding.entry_id == entry_id
    ).delete()
    
    db.delete(entry)
    db.commit()
    
    return {"success": True, "entry_id": entry_id}
