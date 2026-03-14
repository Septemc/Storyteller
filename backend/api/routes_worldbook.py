from datetime import datetime
import json
import re
import uuid
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, BackgroundTasks, Body, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from ..core.auth import User as AuthUser, get_current_user
from ..core.tenant import current_user_id, owner_only, owner_or_public, resolve_scoped_id
from ..db import models
from ..db.base import SessionLocal, get_db

router = APIRouter()

WORLDBOOK_ID_PATTERN = re.compile(r"^W[a-z0-9]{7}$")


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


def _query_terms(text: str) -> List[str]:
    return [
        term for term in re.findall(r"[\u4e00-\u9fff]|[A-Za-z0-9_]+", (text or "").lower()) if term.strip()
    ]


def _semantic_match_score(query: str, entry: models.WorldbookEntry) -> float:
    query_text = (query or "").strip().lower()
    title = (entry.title or "").lower()
    tags = (entry.tags or "").lower()
    content = (entry.content or "").lower()
    haystack = f"{title} {tags} {content}"

    if not query_text or not haystack.strip():
        return 0.0

    terms = _query_terms(query_text) or [query_text]
    coverage = sum(1 for term in terms if term in haystack) / max(len(terms), 1)
    title_boost = (0.5 if query_text in title else 0.0) + sum(0.08 for term in terms if term in title)
    tag_boost = sum(0.05 for term in terms if term in tags)
    content_boost = sum(0.02 for term in terms if term in content)
    importance_boost = float(entry.importance or 0.0) * 0.1
    exact_bonus = 0.2 if query_text in haystack else 0.0
    return round(coverage + title_boost + tag_boost + content_boost + importance_boost + exact_bonus, 4)


def _normalize_worldbook_id(raw_value: Optional[str]) -> Optional[str]:
    if raw_value is None:
        return None
    value = str(raw_value).strip()
    if not value:
        return None
    if value[:1].lower() == "w":
        value = f"W{value[1:]}"
    if not WORLDBOOK_ID_PATTERN.fullmatch(value):
        raise HTTPException(status_code=400, detail="worldbook_id must match Wxxxxxxx")
    return value


def _generate_worldbook_id(db: Session, user_id: Optional[str]) -> str:
    while True:
        candidate = f"W{uuid.uuid4().hex[:7]}"
        exists = owner_only(
            db.query(models.WorldbookEntry).filter(models.WorldbookEntry.worldbook_id == candidate),
            models.WorldbookEntry,
            user_id,
        ).first()
        if not exists:
            return candidate


def _apply_worldbook_filters(query, user_id: Optional[str], worldbook_id: Optional[str] = None):
    scoped_query = owner_or_public(query, models.WorldbookEntry, user_id)
    if worldbook_id:
        scoped_query = scoped_query.filter(models.WorldbookEntry.worldbook_id == worldbook_id)
    return scoped_query


def _apply_worldbook_write_filters(query, model, user_id: Optional[str], worldbook_id: Optional[str] = None):
    scoped_query = owner_or_public(query, model, user_id)
    if worldbook_id and hasattr(model, "worldbook_id"):
        scoped_query = scoped_query.filter(getattr(model, "worldbook_id") == worldbook_id)
    return scoped_query


def _find_writable_entry(db: Session, entry_id: Optional[str], user_id: Optional[str]) -> Optional[models.WorldbookEntry]:
    if not entry_id:
        return None
    return owner_or_public(
        db.query(models.WorldbookEntry).filter(models.WorldbookEntry.entry_id == entry_id),
        models.WorldbookEntry,
        user_id,
    ).first()


def _parse_entries_payload(payload: Any) -> tuple[List[Dict[str, Any]], Optional[str]]:
    def _extract_entries_from_container(container: Any, fallback_category: Optional[str] = None) -> List[Dict[str, Any]]:
        normalized: List[Dict[str, Any]] = []
        if isinstance(container, list):
            for item in container:
                if isinstance(item, dict):
                    entry = dict(item)
                    if fallback_category and not entry.get("category"):
                        entry["category"] = fallback_category
                    normalized.append(entry)
            return normalized

        if isinstance(container, dict):
            if "title" in container and "content" in container:
                entry = dict(container)
                if fallback_category and not entry.get("category"):
                    entry["category"] = fallback_category
                return [entry]

            if "entries" in container:
                entries_value = container.get("entries")
                if isinstance(entries_value, dict):
                    return _extract_entries_from_container(list(entries_value.values()), fallback_category)
                return _extract_entries_from_container(entries_value, fallback_category)

            if "items" in container:
                return _extract_entries_from_container(container.get("items"), fallback_category)

            for category_name, value in container.items():
                nested_category = fallback_category if category_name in {"name", "description", "meta"} else category_name
                normalized.extend(_extract_entries_from_container(value, nested_category))
            return normalized

        return []

    if isinstance(payload, dict):
        entries = payload.get("entries")
        if entries is None:
            for key in ("items", "data", "payload", "categories", "modules"):
                if key in payload:
                    entries = payload.get(key)
                    break
        if entries is None and "title" in payload and "content" in payload:
            entries = [payload]
        requested_worldbook_id = payload.get("worldbook_id")
    else:
        entries = payload
        requested_worldbook_id = None

    if not isinstance(entries, list):
        entries = _extract_entries_from_container(entries)

    if not isinstance(entries, list):
        raise HTTPException(status_code=400, detail="worldbook import payload must be a list or an object with entries")

    normalized_entries = [item for item in entries if isinstance(item, dict)]
    return normalized_entries, _normalize_worldbook_id(requested_worldbook_id)


def _extract_tags(raw_tags: Any) -> str:
    if isinstance(raw_tags, list):
        return ",".join(str(item) for item in raw_tags)
    if raw_tags is None:
        return ""
    return str(raw_tags)


def _extract_meta(raw: Dict[str, Any]) -> Dict[str, Any]:
    meta = raw.get("meta") or {}
    if not isinstance(meta, dict):
        meta = {}
    if "enabled" not in meta and "enabled" in raw:
        meta["enabled"] = raw.get("enabled")
    if "disable" not in meta and "disable" in raw:
        meta["disable"] = raw.get("disable")
    if "disabled" in raw and "disable" not in meta:
        meta["disable"] = raw.get("disabled")
    return meta


@router.post("/worldbook/import")
def import_worldbook(
    payload: Any = Body(...),
    db: Session = Depends(get_db),
    background_tasks: BackgroundTasks = None,
    sync_embeddings: bool = Query(False),
    current_user: Optional[AuthUser] = Depends(get_current_user),
) -> Dict[str, Any]:
    user_id = current_user_id(current_user)
    entries, requested_worldbook_id = _parse_entries_payload(payload)
    worldbook_id = requested_worldbook_id or _generate_worldbook_id(db, user_id)

    created = 0
    updated = 0
    entries_to_embed: List[models.WorldbookEntry] = []

    for raw in entries:
        title = raw.get("title")
        content = raw.get("content")
        if not title or not content:
            continue

        preferred_entry_id = raw.get("entry_id") or f"WB_{uuid.uuid4().hex[:10]}"
        existing = _find_writable_entry(db, preferred_entry_id, user_id)
        entry_id = existing.entry_id if existing else resolve_scoped_id(
            db,
            models.WorldbookEntry,
            "entry_id",
            preferred_entry_id,
            user_id,
        )

        category = raw.get("category") or None
        tags_str = _extract_tags(raw.get("tags"))
        meta_json = json.dumps(_extract_meta(raw), ensure_ascii=False)

        if existing:
            existing.worldbook_id = worldbook_id
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
            continue

        entry = models.WorldbookEntry(
            user_id=user_id,
            worldbook_id=worldbook_id,
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
        entries_to_embed.append(entry)
        created += 1

    db.commit()

    entry_ids = [entry.entry_id for entry in entries_to_embed]

    def _compute_embeddings(entry_ids_local: List[str], owner_id: Optional[str]) -> None:
        if not entry_ids_local:
            return
        db2 = SessionLocal()
        try:
            from ..core.rag import create_retriever

            retriever = create_retriever(db2, user_id=owner_id)
            for eid in entry_ids_local:
                try:
                    entry = owner_only(
                        db2.query(models.WorldbookEntry).filter(models.WorldbookEntry.entry_id == eid),
                        models.WorldbookEntry,
                        owner_id,
                    ).first()
                    if entry:
                        retriever.compute_entry_embedding(entry, use_cache=False)
                except Exception:
                    continue
        except Exception:
            return
        finally:
            db2.close()

    if entry_ids:
        if sync_embeddings:
            _compute_embeddings(entry_ids, user_id)
        elif background_tasks is not None:
            background_tasks.add_task(_compute_embeddings, entry_ids, user_id)
        else:
            _compute_embeddings(entry_ids, user_id)

    return {
        "worldbook_id": worldbook_id,
        "created_or_updated": created + updated,
        "created": created,
        "updated": updated,
        "embeddings": "queued" if (entry_ids and not sync_embeddings) else "done",
    }


@router.get("/worldbook/list", response_model=WorldbookListResponse)
def list_worldbook(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=2000),
    keyword: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    worldbook_id: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: Optional[AuthUser] = Depends(get_current_user),
) -> WorldbookListResponse:
    user_id = current_user_id(current_user)
    normalized_worldbook_id = _normalize_worldbook_id(worldbook_id)
    query = _apply_worldbook_filters(db.query(models.WorldbookEntry), user_id, normalized_worldbook_id)

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
    rows = query.order_by(models.WorldbookEntry.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()

    items: List[WorldbookListItem] = []
    for row in rows:
        try:
            meta = json.loads(row.meta_json) if row.meta_json else {}
        except Exception:
            meta = {}
        items.append(
            WorldbookListItem(
                worldbook_id=row.worldbook_id,
                entry_id=row.entry_id,
                category=row.category,
                tags=row.tags.split(",") if row.tags else [],
                title=row.title,
                content=row.content,
                importance=row.importance,
                canonical=row.canonical,
                enabled=meta.get("enabled") if isinstance(meta, dict) else None,
                disable=meta.get("disable") if isinstance(meta, dict) else None,
                meta=meta if isinstance(meta, dict) else {},
            )
        )

    return WorldbookListResponse(items=items, page=page, total_pages=total_pages)


@router.get("/worldbook/{entry_id}", response_model=WorldbookDetailResponse)
def get_worldbook_entry(
    entry_id: str,
    db: Session = Depends(get_db),
    current_user: Optional[AuthUser] = Depends(get_current_user),
) -> WorldbookDetailResponse:
    user_id = current_user_id(current_user)
    entry = _apply_worldbook_filters(
        db.query(models.WorldbookEntry).filter(models.WorldbookEntry.entry_id == entry_id),
        user_id,
    ).first()
    if not entry:
        raise HTTPException(status_code=404, detail="worldbook entry not found")

    try:
        meta = json.loads(entry.meta_json) if entry.meta_json else {}
    except Exception:
        meta = {}

    return WorldbookDetailResponse(
        worldbook_id=entry.worldbook_id,
        entry_id=entry.entry_id,
        category=entry.category,
        tags=entry.tags.split(",") if entry.tags else [],
        title=entry.title,
        content=entry.content,
        importance=entry.importance,
        canonical=entry.canonical,
        meta=meta if isinstance(meta, dict) else {},
    )


@router.post("/worldbook/semantic_search", response_model=WorldbookSemanticSearchResponse)
def semantic_search_worldbook(
    payload: WorldbookSemanticSearchRequest,
    db: Session = Depends(get_db),
    current_user: Optional[AuthUser] = Depends(get_current_user),
) -> WorldbookSemanticSearchResponse:
    user_id = current_user_id(current_user)
    normalized_worldbook_id = _normalize_worldbook_id(payload.worldbook_id)
    query = _apply_worldbook_filters(db.query(models.WorldbookEntry), user_id, normalized_worldbook_id)

    if payload.category:
        query = query.filter(models.WorldbookEntry.category == payload.category)

    entries = query.all()
    if not entries or not payload.query.strip():
        return WorldbookSemanticSearchResponse(results=[])

    ranked: List[WorldbookSemanticSearchItem] = []
    for entry in entries:
        score = _semantic_match_score(payload.query, entry)
        if score <= 0:
            continue
        ranked.append(
            WorldbookSemanticSearchItem(
                worldbook_id=entry.worldbook_id,
                entry_id=entry.entry_id,
                category=entry.category,
                title=entry.title,
                content=entry.content,
                importance=entry.importance,
                relevance_score=score,
            )
        )

    ranked.sort(key=lambda item: item.relevance_score, reverse=True)
    return WorldbookSemanticSearchResponse(results=ranked[: max(payload.top_k, 1)])


@router.delete("/worldbook/category")
def delete_worldbook_category(
    category: str = Query(...),
    worldbook_id: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: Optional[AuthUser] = Depends(get_current_user),
) -> Dict[str, Any]:
    user_id = current_user_id(current_user)
    normalized_worldbook_id = _normalize_worldbook_id(worldbook_id)
    query = _apply_worldbook_write_filters(
        db.query(models.WorldbookEntry).filter(models.WorldbookEntry.category == category),
        models.WorldbookEntry,
        user_id,
        normalized_worldbook_id,
    )

    entries = query.all()
    if not entries:
        return {"success": True, "deleted": 0}

    entry_ids = [entry.entry_id for entry in entries]
    delete_embeddings = _apply_worldbook_write_filters(
        db.query(models.WorldbookEmbedding),
        models.WorldbookEmbedding,
        user_id,
        normalized_worldbook_id,
    ).filter(
        models.WorldbookEmbedding.entry_id.in_(entry_ids)
    )
    delete_embeddings.delete(synchronize_session=False)

    deleted_count = query.delete(synchronize_session=False)
    db.commit()
    return {"success": True, "deleted": deleted_count, "worldbook_id": normalized_worldbook_id}


@router.delete("/worldbook/all")
def delete_all_worldbook_entries(
    confirm: bool = Query(False),
    worldbook_id: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: Optional[AuthUser] = Depends(get_current_user),
) -> Dict[str, Any]:
    if not confirm:
        raise HTTPException(status_code=400, detail="confirm=true is required")

    user_id = current_user_id(current_user)
    normalized_worldbook_id = _normalize_worldbook_id(worldbook_id)
    query = _apply_worldbook_write_filters(
        db.query(models.WorldbookEntry),
        models.WorldbookEntry,
        user_id,
        normalized_worldbook_id,
    )

    entries = query.all()
    delete_embeddings = _apply_worldbook_write_filters(
        db.query(models.WorldbookEmbedding),
        models.WorldbookEmbedding,
        user_id,
        normalized_worldbook_id,
    )
    if entries and not normalized_worldbook_id:
        entry_ids = [entry.entry_id for entry in entries]
        delete_embeddings = delete_embeddings.filter(models.WorldbookEmbedding.entry_id.in_(entry_ids))
    delete_embeddings.delete(synchronize_session=False)

    if not entries:
        db.commit()
        return {"success": True, "deleted": 0, "worldbook_id": normalized_worldbook_id}

    deleted_count = query.delete(synchronize_session=False)
    db.commit()
    return {"success": True, "deleted": deleted_count, "worldbook_id": normalized_worldbook_id}


@router.delete("/worldbook/{entry_id}")
def delete_worldbook_entry(
    entry_id: str,
    db: Session = Depends(get_db),
    current_user: Optional[AuthUser] = Depends(get_current_user),
) -> Dict[str, Any]:
    user_id = current_user_id(current_user)
    entry = owner_or_public(
        db.query(models.WorldbookEntry).filter(models.WorldbookEntry.entry_id == entry_id),
        models.WorldbookEntry,
        user_id,
    ).first()
    if not entry:
        raise HTTPException(status_code=404, detail="worldbook entry not found")

    owner_or_public(
        db.query(models.WorldbookEmbedding).filter(models.WorldbookEmbedding.entry_id == entry_id),
        models.WorldbookEmbedding,
        user_id,
    ).delete(synchronize_session=False)

    db.delete(entry)
    db.commit()
    return {"success": True, "entry_id": entry_id, "worldbook_id": entry.worldbook_id}
