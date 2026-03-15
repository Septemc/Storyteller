from __future__ import annotations

from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from ....core.auth import User as AuthUser, get_current_user_sync
from ....core.tenant import current_user_id
from ....db.base import get_db
from ..services.store import character_payload, export_character_rows, get_character_row, list_character_items, owner_character_query, upsert_character
from .schemas import CharacterDetailResponse, CharacterListResponse

router = APIRouter()


@router.post("/characters/import")
def import_characters(
    payload: Dict[str, Any],
    db: Session = Depends(get_db),
    current_user: Optional[AuthUser] = Depends(get_current_user_sync),
):
    owner_id = current_user_id(current_user)
    raw_items = payload.get("items") if isinstance(payload.get("items"), list) else [payload]
    imported = []
    for item in raw_items:
        record = upsert_character(db, owner_id, item)
        imported.append({"session_id": record.session_id, "character_id": record.character_id})
    db.commit()
    return {"ok": True, "imported": imported}


@router.get("/characters/export/all")
def export_all_characters(
    session_id: str = Query(..., description="session id"),
    db: Session = Depends(get_db),
    current_user: Optional[AuthUser] = Depends(get_current_user_sync),
):
    owner_id = current_user_id(current_user)
    return {"items": export_character_rows(db, owner_id, session_id)}


@router.get("/characters/{character_id}", response_model=CharacterDetailResponse)
def get_character(
    character_id: str,
    session_id: str = Query(..., description="session id"),
    db: Session = Depends(get_db),
    current_user: Optional[AuthUser] = Depends(get_current_user_sync),
):
    owner_id = current_user_id(current_user)
    row = get_character_row(db, owner_id, session_id, character_id)
    if not row:
        raise HTTPException(status_code=404, detail="character not found")
    return character_payload(row, db, owner_id)


@router.get("/characters", response_model=CharacterListResponse)
def list_characters(
    session_id: str = Query(..., description="session id"),
    q: str = Query("", description="keyword"),
    db: Session = Depends(get_db),
    current_user: Optional[AuthUser] = Depends(get_current_user_sync),
):
    return CharacterListResponse(items=list_character_items(db, current_user_id(current_user), session_id, q=q))


@router.delete("/characters/clear_all")
def clear_all_characters(
    session_id: str = Query(..., description="session id"),
    db: Session = Depends(get_db),
    current_user: Optional[AuthUser] = Depends(get_current_user_sync),
):
    owner_character_query(db, current_user_id(current_user), session_id).delete()
    db.commit()
    return {"ok": True}


@router.put("/characters/{character_id}", response_model=CharacterDetailResponse)
def update_character(
    character_id: str,
    payload: Dict[str, Any],
    db: Session = Depends(get_db),
    current_user: Optional[AuthUser] = Depends(get_current_user_sync),
):
    owner_id = current_user_id(current_user)
    payload["character_id"] = character_id
    row = upsert_character(db, owner_id, payload)
    db.commit()
    return character_payload(row, db, owner_id)


@router.delete("/characters/{character_id}")
def delete_character(
    character_id: str,
    session_id: str = Query(..., description="session id"),
    db: Session = Depends(get_db),
    current_user: Optional[AuthUser] = Depends(get_current_user_sync),
):
    owner_id = current_user_id(current_user)
    row = get_character_row(db, owner_id, session_id, character_id)
    if not row:
        raise HTTPException(status_code=404, detail="character not found")
    db.delete(row)
    db.commit()
    return {"ok": True}
