from __future__ import annotations

import json
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, BackgroundTasks, Body, Depends, Query
from sqlalchemy.orm import Session

from ....core.auth import User as AuthUser, get_current_user
from ....core.tenant import current_user_id, owner_only
from ....db import models
from ....db.base import SessionLocal, get_db
from .helpers import extract_meta, extract_tags, find_writable_entry, generate_worldbook_id, parse_entries_payload, resolve_entry_id

router = APIRouter()


@router.post("/worldbook/import")
def import_worldbook(payload: Any = Body(...), db: Session = Depends(get_db), background_tasks: BackgroundTasks = None, sync_embeddings: bool = Query(False), current_user: Optional[AuthUser] = Depends(get_current_user)) -> Dict[str, Any]:
    user_id = current_user_id(current_user)
    entries, requested_worldbook_id = parse_entries_payload(payload)
    worldbook_id = requested_worldbook_id or generate_worldbook_id(db, user_id)
    created = 0
    updated = 0
    entries_to_embed: List[models.WorldbookEntry] = []
    for raw in entries:
        if not raw.get("title") or not raw.get("content"):
            continue
        preferred_entry_id = raw.get("entry_id") or f"WB_{uuid.uuid4().hex[:10]}"
        existing = find_writable_entry(db, preferred_entry_id, user_id)
        entry_id = existing.entry_id if existing else resolve_entry_id(db, preferred_entry_id, user_id)
        if existing:
            _update_existing_entry(existing, raw, worldbook_id)
            entries_to_embed.append(existing)
            updated += 1
        else:
            entry = models.WorldbookEntry(user_id=user_id, worldbook_id=worldbook_id, entry_id=entry_id, category=raw.get("category") or None, tags=extract_tags(raw.get("tags")), title=raw["title"], content=raw["content"], importance=float(raw.get("importance", 0.5)), canonical=bool(raw.get("canonical", False)), meta_json=json.dumps(extract_meta(raw), ensure_ascii=False), created_at=datetime.utcnow(), updated_at=datetime.utcnow())
            db.add(entry)
            entries_to_embed.append(entry)
            created += 1
    db.commit()
    entry_ids = [entry.entry_id for entry in entries_to_embed]
    if entry_ids:
        if sync_embeddings:
            _compute_embeddings(entry_ids, user_id)
        elif background_tasks is not None:
            background_tasks.add_task(_compute_embeddings, entry_ids, user_id)
        else:
            _compute_embeddings(entry_ids, user_id)
    return {"worldbook_id": worldbook_id, "created_or_updated": created + updated, "created": created, "updated": updated, "embeddings": "queued" if (entry_ids and not sync_embeddings) else "done"}


def _update_existing_entry(existing: models.WorldbookEntry, raw: Dict[str, Any], worldbook_id: str) -> None:
    existing.worldbook_id = worldbook_id
    existing.category = raw.get("category") or None
    existing.tags = extract_tags(raw.get("tags"))
    existing.title = raw["title"]
    existing.content = raw["content"]
    existing.importance = float(raw.get("importance", existing.importance or 0.5))
    existing.canonical = bool(raw.get("canonical", existing.canonical or False))
    existing.meta_json = json.dumps(extract_meta(raw), ensure_ascii=False)
    existing.updated_at = datetime.utcnow()


def _compute_embeddings(entry_ids_local: List[str], owner_id: Optional[str]) -> None:
    db2 = SessionLocal()
    try:
        from ....core.rag import create_retriever

        retriever = create_retriever(db2, user_id=owner_id)
        for entry_id in entry_ids_local:
            entry = owner_only(db2.query(models.WorldbookEntry).filter(models.WorldbookEntry.entry_id == entry_id), models.WorldbookEntry, owner_id).first()
            if entry:
                try:
                    retriever.compute_entry_embedding(entry, use_cache=False)
                except Exception:
                    continue
    finally:
        db2.close()
