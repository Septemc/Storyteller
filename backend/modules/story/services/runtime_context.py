from __future__ import annotations

import json
import re
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy.orm import Session

from ....core.session_state import ensure_session_state
from ....core.tenant import owner_only
from ....db import models
from ...characters.services.profile_utils import extract_basic_summary, is_inactive_name
from ...characters.services.store import character_payload
from .helpers import safe_json_loads, settings_key


def load_worldbook_runtime_state(db: Session, user_id: Optional[str]) -> Tuple[Optional[str], Dict[str, bool]]:
    row = owner_only(
        db.query(models.GlobalSetting).filter(models.GlobalSetting.key == settings_key(user_id)),
        models.GlobalSetting,
        user_id,
    ).first()
    if not row and user_id:
        row = owner_only(
            db.query(models.GlobalSetting).filter(models.GlobalSetting.key == "global"),
            models.GlobalSetting,
            user_id,
        ).first()
    worldbook = safe_json_loads(row.value_json if row else None, {}).get("worldbook", {})
    active_worldbook_id = str(worldbook.get("active_worldbook_id") or "").strip() or None
    switches = {
        str(key).strip(): value is not False
        for key, value in (worldbook.get("category_switches") or {}).items()
        if str(key).strip()
    }
    return active_worldbook_id, switches


def entry_enabled_for_story(entry: models.WorldbookEntry, category_switches: Optional[Dict[str, bool]] = None) -> bool:
    meta = safe_json_loads(entry.meta_json, {})
    category_key = f"{entry.worldbook_id}::{(entry.category or '').strip()}"
    enabled = meta.get("enabled", True) is not False and not bool(meta.get("disable") or meta.get("disabled"))
    return enabled and category_switches.get(category_key, True) is not False if category_switches else enabled


def get_or_create_session_state(db: Session, session_id: str, user_id: Optional[str] = None) -> models.SessionState:
    return ensure_session_state(db, session_id, user_id=user_id)


def character_profile_from_row(db: Session, row: models.Character, user_id: Optional[str]) -> Dict[str, Any]:
    payload = character_payload(row, db, user_id)
    summary = extract_basic_summary(payload["full_profile"])
    summary["template_id"] = row.template_id
    return summary


def pick_main_character(db: Session, session_id: str, preferred_character_id: Optional[str] = None, user_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
    row = owner_only(
        db.query(models.Character).filter(models.Character.session_id == session_id, models.Character.character_id == preferred_character_id),
        models.Character,
        user_id,
    ).first() if preferred_character_id else None
    if not row:
        row = owner_only(
            db.query(models.Character).filter(models.Character.session_id == session_id),
            models.Character,
            user_id,
        ).first()
    return character_profile_from_row(db, row, user_id) if row else None


def character_brief(profile: Dict[str, Any], max_len: int = 120) -> str:
    raw = profile.get("raw_basic") or {}
    parts = []
    if raw.get("f_occ") or raw.get("occupation"):
        parts.append(f"occupation:{raw.get('f_occ') or raw.get('occupation')}")
    if raw.get("f_fac") or raw.get("f_faction"):
        parts.append(f"faction:{raw.get('f_fac') or raw.get('f_faction')}")
    tags = raw.get("f_tags") or raw.get("tags")
    if isinstance(tags, list) and tags:
        parts.append("tags:" + ",".join(str(item) for item in tags[:3]))
    text = "; ".join(parts)
    return text[: max_len - 1] + "…" if len(text) > max_len else text


def character_roster_snippets(
    db: Session,
    session_id: str,
    user_id: Optional[str],
    limit: int = 5,
    context_text: Optional[str] = None,
    exclude_character_id: Optional[str] = None,
) -> List[Dict[str, Any]]:
    rows = owner_only(
        db.query(models.Character).filter(models.Character.session_id == session_id),
        models.Character,
        user_id,
    ).all()
    tokens = re.findall(r"[A-Za-z0-9_]{2,}|[\u4e00-\u9fff]{2,}", (context_text or "").strip())
    scored = []
    for row in rows:
        profile = character_profile_from_row(db, row, user_id)
        if is_inactive_name(profile.get("name") or ""):
            continue
        if exclude_character_id and str(profile.get("character_id") or "") == str(exclude_character_id):
            continue
        search_blob = " ".join(
            [
                str(profile.get("character_id") or ""),
                str(profile.get("name") or ""),
                json.dumps(profile.get("raw_basic") or {}, ensure_ascii=False),
            ]
        )
        score = 0
        if profile.get("name") and profile["name"] in (context_text or ""):
            score += 100
        if str(profile.get("character_id") or "") in (context_text or ""):
            score += 80
        score += sum(3 for token in tokens if token in search_blob)
        scored.append((score, profile))
    scored.sort(key=lambda item: item[0], reverse=True)
    return [item for _, item in scored[:limit]]
