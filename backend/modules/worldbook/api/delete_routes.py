from __future__ import annotations

from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from ....core.auth import User as AuthUser, get_current_user
from ....core.tenant import current_user_id, owner_or_public
from ....db import models
from ....db.base import get_db
from .helpers import apply_worldbook_write_filters, normalize_worldbook_id

router = APIRouter()


@router.delete("/worldbook/category")
def delete_worldbook_category(category: str = Query(...), worldbook_id: Optional[str] = Query(None), db: Session = Depends(get_db), current_user: Optional[AuthUser] = Depends(get_current_user)) -> Dict[str, Any]:
    user_id = current_user_id(current_user)
    normalized_worldbook_id = normalize_worldbook_id(worldbook_id)
    query = apply_worldbook_write_filters(db.query(models.WorldbookEntry).filter(models.WorldbookEntry.category == category), models.WorldbookEntry, user_id, normalized_worldbook_id)
    entries = query.all()
    if not entries:
        return {"success": True, "deleted": 0}
    entry_ids = [entry.entry_id for entry in entries]
    apply_worldbook_write_filters(db.query(models.WorldbookEmbedding), models.WorldbookEmbedding, user_id, normalized_worldbook_id).filter(models.WorldbookEmbedding.entry_id.in_(entry_ids)).delete(synchronize_session=False)
    deleted_count = query.delete(synchronize_session=False)
    db.commit()
    return {"success": True, "deleted": deleted_count, "worldbook_id": normalized_worldbook_id}


@router.delete("/worldbook/all")
def delete_all_worldbook_entries(confirm: bool = Query(False), worldbook_id: Optional[str] = Query(None), db: Session = Depends(get_db), current_user: Optional[AuthUser] = Depends(get_current_user)) -> Dict[str, Any]:
    if not confirm:
        raise HTTPException(status_code=400, detail="confirm=true is required")
    user_id = current_user_id(current_user)
    normalized_worldbook_id = normalize_worldbook_id(worldbook_id)
    query = apply_worldbook_write_filters(db.query(models.WorldbookEntry), models.WorldbookEntry, user_id, normalized_worldbook_id)
    entries = query.all()
    delete_embeddings = apply_worldbook_write_filters(db.query(models.WorldbookEmbedding), models.WorldbookEmbedding, user_id, normalized_worldbook_id)
    if entries and not normalized_worldbook_id:
        delete_embeddings = delete_embeddings.filter(models.WorldbookEmbedding.entry_id.in_([entry.entry_id for entry in entries]))
    delete_embeddings.delete(synchronize_session=False)
    if not entries:
        db.commit()
        return {"success": True, "deleted": 0, "worldbook_id": normalized_worldbook_id}
    deleted_count = query.delete(synchronize_session=False)
    db.commit()
    return {"success": True, "deleted": deleted_count, "worldbook_id": normalized_worldbook_id}


@router.delete("/worldbook/{entry_id}")
def delete_worldbook_entry(entry_id: str, db: Session = Depends(get_db), current_user: Optional[AuthUser] = Depends(get_current_user)) -> Dict[str, Any]:
    user_id = current_user_id(current_user)
    entry = owner_or_public(db.query(models.WorldbookEntry).filter(models.WorldbookEntry.entry_id == entry_id), models.WorldbookEntry, user_id).first()
    if not entry:
        raise HTTPException(status_code=404, detail="worldbook entry not found")
    owner_or_public(db.query(models.WorldbookEmbedding).filter(models.WorldbookEmbedding.entry_id == entry_id), models.WorldbookEmbedding, user_id).delete(synchronize_session=False)
    db.delete(entry)
    db.commit()
    return {"success": True, "entry_id": entry_id, "worldbook_id": entry.worldbook_id}
