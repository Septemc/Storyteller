from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy.orm import Session

from ....core.tenant import owner_only, owner_or_public
from ....db import models
from .content_parser import extract_story_parts
from .runtime_context import entry_enabled_for_story, get_or_create_session_state, load_worldbook_runtime_state, pick_main_character


def worldbook_snippets(db: Session, user_id: Optional[str], context_text: Optional[str] = None, limit: int = 8, active_worldbook_id: Optional[str] = None, category_switches: Optional[Dict[str, bool]] = None) -> List[Dict[str, Any]]:
    if context_text:
        try:
            from ....modules.knowledge.services.retrieval_queries import create_retriever, retrieve_for_story

            disabled = {key.split("::", 1)[1] for key, enabled in (category_switches or {}).items() if active_worldbook_id and key.startswith(f"{active_worldbook_id}::") and enabled is False and "::" in key}
            results = retrieve_for_story(create_retriever(db, user_id=user_id, worldbook_id=active_worldbook_id, disabled_categories=disabled), context_text, top_k=limit)
            filtered = []
            for result in results:
                query = db.query(models.WorldbookEntry).filter(models.WorldbookEntry.entry_id == result.get("entry_id"))
                if active_worldbook_id:
                    query = query.filter(models.WorldbookEntry.worldbook_id == active_worldbook_id)
                entry = owner_or_public(query, models.WorldbookEntry, user_id).first()
                if entry and entry_enabled_for_story(entry, category_switches):
                    filtered.append(result)
            if filtered:
                return filtered
        except Exception:
            pass
    rows = owner_or_public(db.query(models.WorldbookEntry), models.WorldbookEntry, user_id)
    rows = rows.filter(models.WorldbookEntry.worldbook_id == active_worldbook_id) if active_worldbook_id else rows
    rows = rows.order_by(models.WorldbookEntry.importance.desc(), models.WorldbookEntry.updated_at.desc()).limit(limit * 3).all()
    return [{"worldbook_id": row.worldbook_id, "entry_id": row.entry_id, "title": row.title, "category": row.category, "content": (row.content or "")[:800]} for row in rows if entry_enabled_for_story(row, category_switches)][:limit]


def dungeon_context(db: Session, state: models.SessionState, user_id: Optional[str]) -> Tuple[Optional[models.Dungeon], Optional[models.DungeonNode]]:
    dungeon = owner_only(db.query(models.Dungeon).filter(models.Dungeon.dungeon_id == state.current_dungeon_id), models.Dungeon, user_id).first() if state.current_dungeon_id else None
    dungeon = dungeon or owner_only(db.query(models.Dungeon), models.Dungeon, user_id).first()
    if not dungeon:
        return None, None
    node = None
    if state.current_node_id:
        node = db.query(models.DungeonNode).filter(models.DungeonNode.dungeon_id == dungeon.dungeon_id, models.DungeonNode.node_id == state.current_node_id).first()
    node = node or (dungeon.nodes[0] if dungeon.nodes else None)
    return dungeon, node


def build_dungeon_progress_hint(dungeon: Optional[models.Dungeon], node: Optional[models.DungeonNode]) -> Optional[str]:
    if not dungeon:
        return None
    if node and node.progress_percent is not None:
        return f"节点进度 {max(0, min(100, int(node.progress_percent)))}%"
    return f"节点 {int(node.index_in_dungeon) + 1}/{len(dungeon.nodes or [])}" if node and dungeon.nodes else "未设置节点进度"


def build_session_runtime_context(db: Session, session_id: str, user_id: Optional[str] = None) -> Dict[str, Any]:
    state = get_or_create_session_state(db, session_id, user_id=user_id)
    global_state = {} if not state.global_state_json else __import__("json").loads(state.global_state_json)
    main_character = pick_main_character(db, session_id=session_id, preferred_character_id=global_state.get("main_character_id"), user_id=user_id)
    dungeon, node = dungeon_context(db, state, user_id)
    dungeon_ctx = {"id": dungeon.dungeon_id, "name": dungeon.name, "node_name": node.name if node else None, "progress_hint": build_dungeon_progress_hint(dungeon, node)} if dungeon else None
    return {"session_state": state, "global_state": global_state, "main_character": main_character, "dungeon": dungeon_ctx}


def recent_story(db: Session, session_id: str, user_id: Optional[str], limit: int = 6) -> List[str]:
    rows = owner_only(db.query(models.StorySegment).filter(models.StorySegment.session_id == session_id), models.StorySegment, user_id).order_by(models.StorySegment.order_index.desc()).limit(limit).all()
    items: List[str] = []
    for row in reversed(rows):
        text = _story_only_text(row)
        if text:
            items.append(text)
    return items


def _story_only_text(row: models.StorySegment) -> str:
    if row.content_story and row.content_story.strip():
        return row.content_story.strip()
    parts = extract_story_parts(row.text or "")
    if parts.get("story"):
        return parts["story"].strip()
    return (row.text or "").strip()
