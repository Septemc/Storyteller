from __future__ import annotations

import json
import re
import uuid
from typing import Any, Dict, List, Optional, Tuple

from fastapi import HTTPException
from sqlalchemy.orm import Session

from ....core.tenant import owner_only, owner_or_public, resolve_scoped_id
from ....db import models

WORLDBOOK_ID_PATTERN = re.compile(r"^W[a-z0-9]{7}$")


def query_terms(text: str) -> List[str]:
    return [term for term in re.findall(r"[\u4e00-\u9fff]|[A-Za-z0-9_]+", (text or "").lower()) if term.strip()]


def semantic_match_score(query: str, entry: models.WorldbookEntry) -> float:
    query_text = (query or "").strip().lower()
    haystack = f"{(entry.title or '').lower()} {(entry.tags or '').lower()} {(entry.content or '').lower()}"
    if not query_text or not haystack.strip():
        return 0.0
    terms = query_terms(query_text) or [query_text]
    coverage = sum(1 for term in terms if term in haystack) / max(len(terms), 1)
    title_boost = (0.5 if query_text in (entry.title or "").lower() else 0.0) + sum(0.08 for term in terms if term in (entry.title or "").lower())
    tag_boost = sum(0.05 for term in terms if term in (entry.tags or "").lower())
    content_boost = sum(0.02 for term in terms if term in (entry.content or "").lower())
    return round(coverage + title_boost + tag_boost + content_boost + float(entry.importance or 0.0) * 0.1 + (0.2 if query_text in haystack else 0.0), 4)


def normalize_worldbook_id(raw_value: Optional[str]) -> Optional[str]:
    if raw_value is None or not str(raw_value).strip():
        return None
    value = str(raw_value).strip()
    if value[:1].lower() == "w":
        value = f"W{value[1:]}"
    if not WORLDBOOK_ID_PATTERN.fullmatch(value):
        raise HTTPException(status_code=400, detail="worldbook_id must match Wxxxxxxx")
    return value


def generate_worldbook_id(db: Session, user_id: Optional[str]) -> str:
    while True:
        candidate = f"W{uuid.uuid4().hex[:7]}"
        if not owner_only(db.query(models.WorldbookEntry).filter(models.WorldbookEntry.worldbook_id == candidate), models.WorldbookEntry, user_id).first():
            return candidate


def apply_worldbook_filters(query, user_id: Optional[str], worldbook_id: Optional[str] = None):
    scoped_query = owner_or_public(query, models.WorldbookEntry, user_id)
    return scoped_query.filter(models.WorldbookEntry.worldbook_id == worldbook_id) if worldbook_id else scoped_query


def apply_worldbook_write_filters(query, model, user_id: Optional[str], worldbook_id: Optional[str] = None):
    scoped_query = owner_or_public(query, model, user_id)
    if worldbook_id and hasattr(model, "worldbook_id"):
        scoped_query = scoped_query.filter(getattr(model, "worldbook_id") == worldbook_id)
    return scoped_query


def find_writable_entry(db: Session, entry_id: Optional[str], user_id: Optional[str]) -> Optional[models.WorldbookEntry]:
    if not entry_id:
        return None
    return owner_or_public(db.query(models.WorldbookEntry).filter(models.WorldbookEntry.entry_id == entry_id), models.WorldbookEntry, user_id).first()


def parse_entries_payload(payload: Any) -> Tuple[List[Dict[str, Any]], Optional[str]]:
    entries, requested_worldbook_id = _extract_entries_and_id(payload)
    if not isinstance(entries, list):
        raise HTTPException(status_code=400, detail="worldbook import payload must be a list or an object with entries")
    return [item for item in entries if isinstance(item, dict)], normalize_worldbook_id(requested_worldbook_id)


def extract_tags(raw_tags: Any) -> str:
    return ",".join(str(item) for item in raw_tags) if isinstance(raw_tags, list) else ("" if raw_tags is None else str(raw_tags))


def extract_meta(raw: Dict[str, Any]) -> Dict[str, Any]:
    meta = raw.get("meta") if isinstance(raw.get("meta"), dict) else {}
    if "enabled" not in meta and "enabled" in raw:
        meta["enabled"] = raw.get("enabled")
    if "disable" not in meta and "disable" in raw:
        meta["disable"] = raw.get("disable")
    if "disabled" in raw and "disable" not in meta:
        meta["disable"] = raw.get("disabled")
    return meta


def resolve_entry_id(db: Session, preferred_entry_id: str, user_id: Optional[str]) -> str:
    return resolve_scoped_id(db, models.WorldbookEntry, "entry_id", preferred_entry_id, user_id)


def _extract_entries_and_id(payload: Any) -> Tuple[Any, Any]:
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
        return _extract_entries_from_container(entries), requested_worldbook_id
    return payload, None


def _extract_entries_from_container(container: Any, fallback_category: Optional[str] = None) -> List[Dict[str, Any]]:
    if isinstance(container, list):
        return [dict(item, category=item.get("category") or fallback_category) if isinstance(item, dict) else {} for item in container if isinstance(item, dict)]
    if isinstance(container, dict):
        if "title" in container and "content" in container:
            return [dict(container, category=container.get("category") or fallback_category)]
        if "entries" in container:
            return _extract_entries_from_container(container.get("entries"), fallback_category)
        if "items" in container:
            return _extract_entries_from_container(container.get("items"), fallback_category)
        results: List[Dict[str, Any]] = []
        for category_name, value in container.items():
            nested_category = fallback_category if category_name in {"name", "description", "meta"} else category_name
            results.extend(_extract_entries_from_container(value, nested_category))
        return results
    return []
