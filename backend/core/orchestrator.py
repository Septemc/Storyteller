from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from time import perf_counter
from typing import Any, Dict, Generator, List, Optional, Tuple

from sqlalchemy.orm import Session

from ..db import models
from .session_state import ensure_session_state
from . import prompts, storage
from .llm_client import LLMError, chat_completion
from .tenant import owner_only, owner_or_public


@dataclass
class GenerateMeta:
    scene_title: str = ""
    tags: List[str] = None
    tone: Optional[str] = None
    pacing: Optional[str] = None
    dungeon_progress_hint: Optional[str] = None
    dungeon_name: Optional[str] = None
    dungeon_node_name: Optional[str] = None
    main_character: Optional[Dict[str, Any]] = None
    word_count: Optional[int] = None
    duration_ms: Optional[int] = None


OUTPUT_FORMAT_CONSTRAINT_PATH = Path(__file__).with_name("output_format_constraint.txt")
CONTENT_TAGS = ["思考过程", "正文部分", "内容总结", "行动选项"]


def _safe_json_loads(value: Optional[str], default: Any) -> Any:
    if not value:
        return default
    try:
        return json.loads(value)
    except Exception:
        return default


def _first_non_empty(data: Dict[str, Any], keys: List[str]) -> Optional[str]:
    for key in keys:
        value = data.get(key)
        if value is None:
            continue
        text = str(value).strip()
        if text:
            return text
    return None


def _settings_key(user_id: Optional[str]) -> str:
    if user_id:
        return f"global::{user_id}"
    return "global::public"


def _load_worldbook_runtime_state(db: Session, user_id: Optional[str]) -> Tuple[Optional[str], Dict[str, bool]]:
    row = owner_only(
        db.query(models.GlobalSetting).filter(models.GlobalSetting.key == _settings_key(user_id)),
        models.GlobalSetting,
        user_id,
    ).first()
    if not row and user_id:
        row = owner_only(
            db.query(models.GlobalSetting).filter(models.GlobalSetting.key == "global"),
            models.GlobalSetting,
            user_id,
        ).first()

    data = _safe_json_loads(row.value_json if row else None, {})
    worldbook = data.get('worldbook') if isinstance(data, dict) else {}
    if not isinstance(worldbook, dict):
        worldbook = {}

    active_worldbook_id = str(worldbook.get('active_worldbook_id') or '').strip() or None
    raw_switches = worldbook.get('category_switches') if isinstance(worldbook.get('category_switches'), dict) else {}
    category_switches: Dict[str, bool] = {}
    for key, value in raw_switches.items():
        normalized_key = str(key).strip()
        if normalized_key:
            category_switches[normalized_key] = value is not False
    return active_worldbook_id, category_switches


def _entry_enabled_for_story(entry: models.WorldbookEntry, category_switches: Optional[Dict[str, bool]] = None) -> bool:
    meta = _safe_json_loads(entry.meta_json, {})
    if not isinstance(meta, dict):
        meta = {}
    enabled = meta.get('enabled', True) is not False
    disabled = bool(meta.get('disable') or meta.get('disabled'))
    if not enabled or disabled:
        return False
    if category_switches:
        category_key = f"{entry.worldbook_id}::{(entry.category or '').strip()}"
        if category_switches.get(category_key, True) is False:
            return False
    return True


def _get_or_create_session_state(
    db: Session,
    session_id: str,
    user_id: Optional[str] = None,
) -> models.SessionState:
    return ensure_session_state(db, session_id, user_id=user_id)


def _character_profile_from_row(row: models.Character) -> Dict[str, Any]:
    basic = _safe_json_loads(row.basic_json, {})
    data = _safe_json_loads(row.data_json, {})

    if isinstance(data, dict):
        data_basic = data.get("tab_basic") or data.get("basic")
        if isinstance(data_basic, dict):
            basic = data_basic

        flat_basic = {
            k: v
            for k, v in data.items()
            if not k.startswith("tab_") and k not in {"character_id", "type", "template_id"}
        }
        if flat_basic:
            merged = dict(flat_basic)
            merged.update(basic if isinstance(basic, dict) else {})
            basic = merged

    if not isinstance(basic, dict):
        basic = {}

    return {
        "character_id": row.character_id,
        "name": _first_non_empty(basic, ["name", "姓名", "角色名", "f_name", "f_nickname", "昵称"]),
        "ability_tier": _first_non_empty(basic, ["ability_tier", "能力评级", "境界", "f_ability_tier", "f_level", "f_realm", "f_stage"]),
        "economy_summary": _first_non_empty(basic, ["economy_summary", "经济", "资源", "f_economy", "f_resources", "f_money", "f_wealth"]),
        "raw_basic": basic,
    }


def _pick_main_character(
    db: Session,
    preferred_character_id: Optional[str] = None,
    user_id: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    row: Optional[models.Character] = None

    if preferred_character_id:
        row = owner_only(
            db.query(models.Character).filter(models.Character.character_id == preferred_character_id),
            models.Character,
            user_id,
        ).first()

    if not row:
        row = owner_only(
            db.query(models.Character).filter(models.Character.type.in_(["pc", "player", "protagonist", "main", "hero"])),
            models.Character,
            user_id,
        ).first()

    if not row:
        row = owner_only(db.query(models.Character), models.Character, user_id).first()

    if not row:
        return None

    return _character_profile_from_row(row)


def _character_brief(profile: Dict[str, Any], max_len: int = 120) -> str:
    raw = profile.get("raw_basic")
    if not isinstance(raw, dict):
        return ""

    parts: List[str] = []
    occupation = raw.get("f_occ") or raw.get("occupation") or raw.get("职业")
    faction = raw.get("f_fac") or raw.get("f_faction") or raw.get("势力")
    tags = raw.get("f_tags") or raw.get("tags")

    if occupation:
        parts.append(f"职业:{occupation}")
    if faction:
        parts.append(f"势力:{faction}")
    if isinstance(tags, list) and tags:
        parts.append("标签:" + ",".join(str(t) for t in tags[:3]))

    text = "；".join(parts)
    if len(text) > max_len:
        return text[: max_len - 1] + "…"
    return text


def _character_roster_snippets(
    db: Session,
    user_id: Optional[str],
    limit: int = 5,
    context_text: Optional[str] = None,
    exclude_character_id: Optional[str] = None,
) -> List[Dict[str, Any]]:
    rows = owner_only(db.query(models.Character), models.Character, user_id).all()
    if not rows:
        return []

    tokens = re.findall(r"[A-Za-z0-9_]{2,}|[\u4e00-\u9fff]{2,}", (context_text or "").strip())
    scored: List[Tuple[int, Dict[str, Any]]] = []

    for row in rows:
        profile = _character_profile_from_row(row)
        character_id = str(profile.get("character_id") or "")
        if exclude_character_id and character_id == str(exclude_character_id):
            continue

        name = str(profile.get("name") or "")
        search_blob = " ".join([character_id, name, json.dumps(profile.get("raw_basic") or {}, ensure_ascii=False)])

        score = 0
        if context_text:
            if name and name in context_text:
                score += 100
            if character_id and character_id in context_text:
                score += 80
            for token in tokens:
                if token in search_blob:
                    score += 3

        scored.append((score, profile))

    scored.sort(key=lambda x: x[0], reverse=True)
    return [item for _, item in scored[:limit]]


def _worldbook_snippets(
    db: Session,
    user_id: Optional[str],
    context_text: Optional[str] = None,
    limit: int = 8,
    active_worldbook_id: Optional[str] = None,
    category_switches: Optional[Dict[str, bool]] = None,
) -> List[Dict[str, Any]]:
    if context_text:
        try:
            from .rag import create_retriever

            disabled_categories = {
                key.split("::", 1)[1]
                for key, enabled in (category_switches or {}).items()
                if active_worldbook_id and key.startswith(f"{active_worldbook_id}::") and enabled is False and "::" in key
            }
            retriever = create_retriever(
                db,
                user_id=user_id,
                worldbook_id=active_worldbook_id,
                disabled_categories=disabled_categories,
            )
            results = retriever.retrieve_for_story(context_text, top_k=limit, use_hybrid=True)
            filtered = []
            for result in results:
                entry_id = result.get("entry_id")
                worldbook_id = result.get("worldbook_id")
                if not entry_id:
                    continue
                entry_query = db.query(models.WorldbookEntry).filter(models.WorldbookEntry.entry_id == entry_id)
                if worldbook_id:
                    entry_query = entry_query.filter(models.WorldbookEntry.worldbook_id == worldbook_id)
                if active_worldbook_id:
                    entry_query = entry_query.filter(models.WorldbookEntry.worldbook_id == active_worldbook_id)
                entry = owner_or_public(entry_query, models.WorldbookEntry, user_id).first()
                if entry and _entry_enabled_for_story(entry, category_switches):
                    filtered.append(result)
            if filtered:
                return filtered
        except Exception:
            pass

    rows_query = owner_or_public(db.query(models.WorldbookEntry), models.WorldbookEntry, user_id)
    if active_worldbook_id:
        rows_query = rows_query.filter(models.WorldbookEntry.worldbook_id == active_worldbook_id)
    rows = rows_query.order_by(
        models.WorldbookEntry.importance.desc(),
        models.WorldbookEntry.updated_at.desc(),
    ).limit(limit * 3).all()

    return [
        {
            "worldbook_id": row.worldbook_id,
            "entry_id": row.entry_id,
            "title": row.title,
            "category": row.category,
            "content": (row.content or "")[:800],
        }
        for row in rows
        if _entry_enabled_for_story(row, category_switches)
    ][:limit]


def _dungeon_context(
    db: Session,
    st: models.SessionState,
    user_id: Optional[str],
) -> Tuple[Optional[models.Dungeon], Optional[models.DungeonNode]]:
    dungeon = None
    node = None

    if st.current_dungeon_id:
        dungeon = owner_only(
            db.query(models.Dungeon).filter(models.Dungeon.dungeon_id == st.current_dungeon_id),
            models.Dungeon,
            user_id,
        ).first()

    if not dungeon:
        dungeon = owner_only(db.query(models.Dungeon), models.Dungeon, user_id).first()

    if dungeon:
        if st.current_node_id:
            node = db.query(models.DungeonNode).filter(
                models.DungeonNode.dungeon_id == dungeon.dungeon_id,
                models.DungeonNode.node_id == st.current_node_id,
            ).first()
        if not node and dungeon.nodes:
            node = dungeon.nodes[0]

    return dungeon, node


def _build_dungeon_progress_hint(
    dungeon: Optional[models.Dungeon],
    node: Optional[models.DungeonNode],
) -> Optional[str]:
    if not dungeon:
        return None
    if node and node.progress_percent is not None:
        clamped = max(0, min(100, int(node.progress_percent)))
        return f"节点进度 {clamped}%"
    total_nodes = len(dungeon.nodes or [])
    if not node or total_nodes <= 0:
        return "未设置节点进度"
    return f"节点 {int(node.index_in_dungeon) + 1}/{total_nodes}"


def build_session_runtime_context(
    db: Session,
    session_id: str,
    user_id: Optional[str] = None,
) -> Dict[str, Any]:
    state = _get_or_create_session_state(db, session_id, user_id=user_id)
    global_state = _safe_json_loads(state.global_state_json, {})
    preferred_character_id = global_state.get("main_character_id")

    main_character = _pick_main_character(db, preferred_character_id=preferred_character_id, user_id=user_id)
    dungeon, node = _dungeon_context(db, state, user_id=user_id)

    dungeon_ctx = None
    if dungeon:
        dungeon_ctx = {
            "id": dungeon.dungeon_id,
            "name": dungeon.name,
            "node_name": node.name if node else None,
            "progress_hint": _build_dungeon_progress_hint(dungeon, node),
        }

    return {
        "session_state": state,
        "global_state": global_state,
        "main_character": main_character,
        "dungeon": dungeon_ctx,
    }


def _recent_story(
    db: Session,
    session_id: str,
    user_id: Optional[str],
    limit: int = 6,
) -> List[str]:
    rows = owner_only(
        db.query(models.StorySegment).filter(models.StorySegment.session_id == session_id),
        models.StorySegment,
        user_id,
    ).order_by(models.StorySegment.order_index.desc()).limit(limit).all()
    return [row.text for row in reversed(rows)]


def _load_output_format_constraint() -> str:
    if not OUTPUT_FORMAT_CONSTRAINT_PATH.exists():
        return ""
    try:
        return OUTPUT_FORMAT_CONSTRAINT_PATH.read_text(encoding="utf-8").strip()
    except Exception:
        return ""


def _build_messages(
    system_prompt: str,
    context: Dict[str, Any],
    history: List[str],
    user_input: str,
) -> List[Dict[str, str]]:
    ctx_lines: List[str] = []

    main_character = context.get("main_character")
    if main_character:
        ctx_lines.append("【主角】")
        ctx_lines.append(f"- id: {main_character.get('character_id')}  名称: {main_character.get('name') or '未知'}")
        if main_character.get("ability_tier"):
            ctx_lines.append(f"- 能力: {main_character.get('ability_tier')}")
        if main_character.get("economy_summary"):
            ctx_lines.append(f"- 资源: {main_character.get('economy_summary')}")

    roster = context.get("characters") or []
    if roster:
        ctx_lines.append("\n【角色库（节选）】")
        for character in roster:
            line = f"- id: {character.get('character_id')}  名称: {character.get('name') or '未知'}"
            if character.get("ability_tier"):
                line += f"  境界: {character.get('ability_tier')}"
            brief = _character_brief(character)
            if brief:
                line += f"  信息: {brief}"
            ctx_lines.append(line)

    worldbook = context.get("worldbook") or []
    if worldbook:
        ctx_lines.append("\n【世界书（节选）】")
        for item in worldbook:
            category = f"[{item.get('category')}] " if item.get("category") else ""
            ctx_lines.append(f"- {category}{item.get('title')}: {item.get('content')}")

    dungeon = context.get("dungeon")
    if dungeon:
        ctx_lines.append("\n【副本】")
        ctx_lines.append(f"- 副本: {dungeon.get('name') or '未命名'}")
        if dungeon.get("node_name"):
            ctx_lines.append(f"- 节点: {dungeon.get('node_name')} 进度: {dungeon.get('progress_hint')}")

    if history:
        ctx_lines.append("\n【近期剧情（节选）】")
        for index, item in enumerate(history[-6:], 1):
            ctx_lines.append(f"({index}) {item[-1200:]}")

    messages: List[Dict[str, str]] = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    if ctx_lines:
        messages.append({"role": "system", "content": "以下是当前故事运行时上下文：\n" + "\n".join(ctx_lines)})

    constraint = _load_output_format_constraint()
    if constraint:
        messages.append({"role": "system", "content": constraint})

    messages.append({"role": "user", "content": user_input})
    return messages


def _build_dev_log_info(
    user_input: str,
    system_prompt: str,
    context: Dict[str, Any],
    history: List[str],
    messages: List[Dict[str, str]],
) -> Dict[str, Any]:
    return {
        "userInput": user_input,
        "systemPrompt": system_prompt,
        "contextInfo": context,
        "historyInfo": history[-6:],
        "messages": messages,
        "fullPrompt": "\n\n".join([f"[{m['role']}]\n{m['content']}" for m in messages]),
    }


def _is_valid_story_content(text: str) -> bool:
    if not text:
        return False
    stripped = text.strip()
    if not stripped:
        return False
    has_any_tag = any(f"<{tag}>" in stripped for tag in CONTENT_TAGS)
    if has_any_tag:
        body_match = re.search(r"<正文部分>(.*?)</正文部分>", stripped, re.DOTALL)
        if body_match and body_match.group(1).strip():
            return True
        thinking_match = re.search(r"<思考过程>(.*?)</思考过程>", stripped, re.DOTALL)
        if thinking_match and thinking_match.group(1).strip():
            return True
        return False
    return len(stripped) >= 10


def is_valid_story_content(text: str) -> bool:
    """Public helper used by route layer to keep validation logic centralized."""
    return _is_valid_story_content(text)


def generate_story_text(
    db: Session,
    session_id: str,
    user_input: str,
    force_stream: Optional[bool] = None,
    user_id: Optional[str] = None,
) -> Tuple[str, GenerateMeta, Optional[Generator[str, None, None]], Dict[str, Any]]:
    started = perf_counter()

    runtime = build_session_runtime_context(db, session_id, user_id=user_id)
    recent_history = _recent_story(db, session_id, user_id=user_id, limit=4)
    rag_context = " ".join([item[-500:] for item in recent_history]) + f" {user_input}"
    active_worldbook_id, category_switches = _load_worldbook_runtime_state(db, user_id)

    context: Dict[str, Any] = {
        "main_character": runtime.get("main_character"),
        "characters": _character_roster_snippets(
            db,
            user_id=user_id,
            limit=6,
            context_text=user_input,
            exclude_character_id=(runtime.get("main_character") or {}).get("character_id"),
        ),
        "worldbook": _worldbook_snippets(db, user_id=user_id, context_text=rag_context, limit=6, active_worldbook_id=active_worldbook_id, category_switches=category_switches),
        "dungeon": runtime.get("dungeon"),
    }

    preset = storage.get_active_preset(db, user_id)
    system_prompt = prompts.compile_system_prompt(preset)
    llm_cfg = storage.get_active_llm_config(db, user_id=user_id)
    llm_active = storage.get_llm_active(db, user_id=user_id)

    messages = _build_messages(system_prompt, context, recent_history, user_input)
    dev_log_info = _build_dev_log_info(
        user_input=user_input,
        system_prompt=system_prompt,
        context=context,
        history=recent_history,
        messages=messages,
    )

    if not llm_cfg:
        text = (
            "【未配置模型】\n"
            "请先在“设置 -> LLM 配置”中添加 base_url 和 api_key，并选择默认模型。\n\n"
            f"你的输入：{user_input}"
        )
        duration_ms = int((perf_counter() - started) * 1000)
        meta = GenerateMeta(
            scene_title="占位输出",
            tags=["no_model"],
            tone="中性",
            pacing="-",
            dungeon_progress_hint=(context.get("dungeon") or {}).get("progress_hint"),
            dungeon_name=(context.get("dungeon") or {}).get("name"),
            dungeon_node_name=(context.get("dungeon") or {}).get("node_name"),
            main_character=context.get("main_character"),
            word_count=len(text),
            duration_ms=duration_ms,
        )
        return text, meta, None, dev_log_info

    base_url = str(llm_cfg.get("base_url") or "")
    api_key = str(llm_cfg.get("api_key") or "")
    model = str(llm_active.get("model") or llm_cfg.get("default_model") or "")
    stream_flag = bool(llm_cfg.get("stream", True))
    if force_stream is not None:
        stream_flag = bool(force_stream)

    if not model:
        text = "【未选择模型】请在“设置 -> LLM 配置”中设置默认模型。"
        duration_ms = int((perf_counter() - started) * 1000)
        meta = GenerateMeta(scene_title="占位输出", tags=["no_model"], word_count=len(text), duration_ms=duration_ms)
        return text, meta, None, dev_log_info

    try:
        full_text, stream_gen = chat_completion(
            base_url=base_url,
            api_key=api_key,
            model=model,
            messages=messages,
            temperature=0.8,
            stream=stream_flag,
            timeout_s=120,
        )
    except LLMError as exc:
        text = f"【模型请求失败】{exc}"
        duration_ms = int((perf_counter() - started) * 1000)
        meta = GenerateMeta(scene_title="错误", tags=["error"], word_count=len(text), duration_ms=duration_ms)
        return text, meta, None, dev_log_info

    duration_ms = int((perf_counter() - started) * 1000)
    meta = GenerateMeta(
        scene_title="新剧情",
        tags=["llm", preset.get("name") if preset else "preset"],
        tone="由预设决定",
        pacing="由预设决定",
        dungeon_progress_hint=(context.get("dungeon") or {}).get("progress_hint"),
        dungeon_name=(context.get("dungeon") or {}).get("name"),
        dungeon_node_name=(context.get("dungeon") or {}).get("node_name"),
        main_character=context.get("main_character"),
        duration_ms=duration_ms,
    )

    if stream_gen is not None:
        return "", meta, stream_gen, dev_log_info

    if not is_valid_story_content(full_text):
        full_text = "【生成结果为空】请重试或调整提示词配置。"
    meta.word_count = len(full_text)
    return full_text, meta, None, dev_log_info


def _extract_tag_content(text: str, tag_name: str) -> Optional[str]:
    pattern = rf"<{tag_name}>(.*?)</{tag_name}>"
    match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
    return match.group(1).strip() if match else None


def extract_story_parts(text: str) -> Dict[str, Optional[str]]:
    """Extract thinking/story/summary/actions by orchestrator tag convention."""
    tags = list(CONTENT_TAGS) + ["", "", "", ""]
    return {
        "thinking": _extract_tag_content(text, tags[0]),
        "story": _extract_tag_content(text, tags[1]),
        "summary": _extract_tag_content(text, tags[2]),
        "actions": _extract_tag_content(text, tags[3]),
    }


def persist_story_segment(
    db: Session,
    session_id: str,
    story_text: str,
    user_input: str = None,
    paragraph_word_count: int = 0,
    frontend_duration: float = 0.0,
    backend_duration: float = 0.0,
    user_id: Optional[str] = None,
) -> int:
    state = _get_or_create_session_state(db, session_id, user_id=user_id)
    if state and not state.user_id and user_id:
        state.user_id = user_id
        db.commit()

    existing_count = owner_only(
        db.query(models.StorySegment).filter(models.StorySegment.session_id == session_id),
        models.StorySegment,
        user_id,
    ).count()
    order_index = existing_count + 1

    last_segment = owner_only(
        db.query(models.StorySegment).filter(models.StorySegment.session_id == session_id),
        models.StorySegment,
        user_id,
    ).order_by(models.StorySegment.order_index.desc()).first()

    cumulative_word_count = (last_segment.cumulative_word_count if last_segment else 0) + paragraph_word_count

    base_segment_id = f"{session_id}_{order_index}"
    segment_id = base_segment_id
    if db.query(models.StorySegment).filter(models.StorySegment.segment_id == segment_id).first():
        owner_part = user_id or "public"
        segment_id = f"{base_segment_id}__{owner_part}"
        suffix = 1
        while db.query(models.StorySegment).filter(models.StorySegment.segment_id == segment_id).first():
            suffix += 1
            segment_id = f"{base_segment_id}__{owner_part}_{suffix}"

    parts = extract_story_parts(story_text)

    segment = models.StorySegment(
        segment_id=segment_id,
        session_id=session_id,
        user_id=user_id,
        order_index=order_index,
        user_input=user_input,
        text=story_text,
        dungeon_id=state.current_dungeon_id,
        dungeon_node_id=state.current_node_id,
        paragraph_word_count=paragraph_word_count,
        cumulative_word_count=cumulative_word_count,
        frontend_duration=frontend_duration,
        backend_duration=backend_duration,
        content_thinking=parts["thinking"],
        content_story=parts["story"],
        content_summary=parts["summary"],
        content_actions=parts["actions"],
        created_at=datetime.utcnow(),
    )
    db.add(segment)

    state.total_word_count = (state.total_word_count or 0) + paragraph_word_count
    db.commit()

    return order_index
