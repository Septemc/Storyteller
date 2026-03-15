from __future__ import annotations

import json
import uuid
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy.orm import Session

from ....core.tenant import owner_only
from ....db import models
from ...story.services.content_parser import extract_story_parts

DEATH_WORDS = ["\u6b7b\u4ea1", "\u8eab\u4ea1", "\u6218\u6b7b", "\u9668\u843d"]
BREAKTHROUGH_WORDS = ["\u7a81\u7834", "\u664b\u5347", "\u8fdb\u9636", "\u8e0f\u5165"]
ITEM_USED_WORDS = ["\u4f7f\u7528", "\u670d\u4e0b", "\u6d88\u8017"]
ITEM_GAINED_WORDS = ["\u83b7\u5f97", "\u62fe\u53d6", "\u5f97\u5230"]
ACTION_OPTION_SNAPSHOT = ("session", "last_action_options")


def load_memory_context(
    db: Session,
    story_id: str,
    session_id: str,
    user_id: Optional[str],
    event_limit: int,
    variable_limit: int,
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    events = owner_only(
        db.query(models.EventLedger).filter(
            models.EventLedger.story_id == story_id,
            models.EventLedger.session_id == session_id,
        ),
        models.EventLedger,
        user_id,
    ).order_by(models.EventLedger.created_at.desc()).limit(event_limit).all()
    snapshots = owner_only(
        db.query(models.VariableStateSnapshot).filter(
            models.VariableStateSnapshot.story_id == story_id,
            models.VariableStateSnapshot.session_id == session_id,
        ),
        models.VariableStateSnapshot,
        user_id,
    ).order_by(models.VariableStateSnapshot.created_at.desc()).limit(variable_limit * 3).all()
    unique: Dict[Tuple[str, str], Dict[str, Any]] = {}
    for row in snapshots:
        key = (row.namespace, row.key)
        if key == ACTION_OPTION_SNAPSHOT:
            continue
        if key not in unique:
            unique[key] = {
                "namespace": row.namespace,
                "key": row.key,
                "value": _load_json(row.value_json, {}),
            }
        if len(unique) >= variable_limit:
            break
    return [_event_row(row) for row in reversed(events)], list(unique.values())


def persist_turn_memory(
    db: Session,
    story_id: str,
    session_id: str,
    segment_id: str,
    user_input: str,
    story_text: str,
    user_id: Optional[str],
) -> Dict[str, Any]:
    parts = extract_story_parts(story_text)
    events = _derive_events(parts, user_input)
    snapshots = _derive_snapshots(parts, story_text)
    for event in events:
        db.add(
            models.EventLedger(
                event_id=f"evt_{uuid.uuid4().hex[:12]}",
                story_id=story_id,
                session_id=session_id,
                segment_id=segment_id,
                event_type=event["event_type"],
                scope=event.get("scope", "session"),
                title=event["title"],
                payload_json=json.dumps(event.get("payload", {}), ensure_ascii=False),
                user_id=user_id,
            )
        )
    for snapshot in snapshots:
        db.add(
            models.VariableStateSnapshot(
                snapshot_id=f"var_{uuid.uuid4().hex[:12]}",
                story_id=story_id,
                session_id=session_id,
                segment_id=segment_id,
                namespace=snapshot["namespace"],
                key=snapshot["key"],
                value_json=json.dumps(snapshot["value"], ensure_ascii=False),
                user_id=user_id,
            )
        )
    db.commit()
    return {"events": events, "snapshots": snapshots}


def _derive_events(parts: Dict[str, str], user_input: str) -> List[Dict[str, Any]]:
    summary = (parts.get("summary") or "")[:240]
    story = parts.get("story") or ""
    events = [
        {
            "event_type": "turn.generated",
            "title": "Turn generated",
            "payload": {"user_input": user_input[:160], "summary": summary},
        }
    ]
    keyword_map = {
        "character.death": DEATH_WORDS,
        "character.breakthrough": BREAKTHROUGH_WORDS,
        "item.used": ITEM_USED_WORDS,
        "item.gained": ITEM_GAINED_WORDS,
    }
    for event_type, words in keyword_map.items():
        if any(word in story or word in summary for word in words):
            events.append(
                {
                    "event_type": event_type,
                    "title": event_type,
                    "payload": {"summary": summary},
                }
            )
    return events


def _derive_snapshots(parts: Dict[str, str], story_text: str) -> List[Dict[str, Any]]:
    summary = (parts.get("summary") or "").strip()
    snapshots: List[Dict[str, Any]] = []
    if summary:
        snapshots.append(
            {
                "namespace": "session",
                "key": "last_summary",
                "value": {"text": summary[:240]},
            }
        )
    if any(word in story_text for word in DEATH_WORDS):
        snapshots.append(
            {
                "namespace": "player",
                "key": "is_dead",
                "value": {"value": True},
            }
        )
    return snapshots


def _event_row(row: models.EventLedger) -> Dict[str, Any]:
    return {
        "event_type": row.event_type,
        "title": row.title,
        "payload": _load_json(row.payload_json, {}),
        "created_at": row.created_at.isoformat() if row.created_at else None,
    }


def _load_json(value: Optional[str], default: Any) -> Any:
    try:
        return json.loads(value) if value else default
    except Exception:
        return default
