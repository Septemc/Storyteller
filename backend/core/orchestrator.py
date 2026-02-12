"""Story orchestrator (minimal).

- 从 DB 读取：角色 / 世界书 / 副本(以及会话当前节点)
- 从 GlobalSetting 读取：active preset / active llm config
- 用 preset 编译 system prompt
- 拼装 messages -> 调用 OpenAI-compatible LLM

本实现目标：让主剧情界面具备“能输入、能输出、能流式”的最小闭环。
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from time import perf_counter
from typing import Any, Dict, Generator, List, Optional, Tuple

from sqlalchemy.orm import Session

from ..db import models
from . import storage
from . import prompts
from .llm_client import LLMError, chat_completion


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


def _safe_json_loads(value: Optional[str], default: Any) -> Any:
    if not value:
        return default
    try:
        return json.loads(value)
    except Exception:
        return default


def _get_or_create_session_state(db: Session, session_id: str) -> models.SessionState:
    st = db.query(models.SessionState).filter(models.SessionState.session_id == session_id).first()
    if not st:
        st = models.SessionState(session_id=session_id, current_dungeon_id=None, current_node_id=None, total_word_count=0)
        db.add(st)
        db.commit()
        db.refresh(st)
    return st


def _pick_main_character(db: Session) -> Optional[Dict[str, Any]]:
    """优先 type=pc/player，否则取第一条。"""
    row = (
        db.query(models.Character)
        .filter(models.Character.type.in_(["pc", "player"]))
        .first()
    )
    if not row:
        row = db.query(models.Character).first()
    if not row:
        return None

    basic = _safe_json_loads(row.basic_json, {})
    data = _safe_json_loads(row.data_json, {})
    # 兼容：tab_basic 或 basic
    basic = data.get("tab_basic") or data.get("basic") or basic
    return {
        "character_id": row.character_id,
        "name": basic.get("name") or basic.get("姓名") or basic.get("角色名"),
        "ability_tier": basic.get("ability_tier") or basic.get("能力评级") or basic.get("境界"),
        "economy_summary": basic.get("economy_summary") or basic.get("经济") or basic.get("资源"),
        "raw_basic": basic,
    }


def _worldbook_snippets(db: Session, limit: int = 8) -> List[Dict[str, Any]]:
    rows = (
        db.query(models.WorldbookEntry)
        .order_by(models.WorldbookEntry.importance.desc(), models.WorldbookEntry.updated_at.desc())
        .limit(limit)
        .all()
    )
    out: List[Dict[str, Any]] = []
    for r in rows:
        out.append({
            "entry_id": r.entry_id,
            "title": r.title,
            "category": r.category,
            "content": (r.content or "")[:800],
        })
    return out


def _dungeon_context(db: Session, st: models.SessionState) -> Tuple[Optional[models.Dungeon], Optional[models.DungeonNode]]:
    dungeon = None
    node = None
    if st.current_dungeon_id:
        dungeon = db.query(models.Dungeon).filter(models.Dungeon.dungeon_id == st.current_dungeon_id).first()

    if not dungeon:
        dungeon = db.query(models.Dungeon).first()

    if dungeon:
        if st.current_node_id:
            node = (
                db.query(models.DungeonNode)
                .filter(
                    models.DungeonNode.dungeon_id == dungeon.dungeon_id,
                    models.DungeonNode.node_id == st.current_node_id,
                )
                .first()
            )
        if not node and dungeon.nodes:
            node = dungeon.nodes[0]

    return dungeon, node


def _recent_story(db: Session, session_id: str, limit: int = 6) -> List[str]:
    rows = (
        db.query(models.StorySegment)
        .filter(models.StorySegment.session_id == session_id)
        .order_by(models.StorySegment.order_index.desc())
        .limit(limit)
        .all()
    )
    # 反转到正序
    return [r.text for r in reversed(rows)]


def _build_messages(system_prompt: str, context: Dict[str, Any], history: List[str], user_input: str) -> List[Dict[str, Any]]:
    # 将结构化 context 压缩成一段可读文本
    ctx_lines: List[str] = []

    mc = context.get("main_character")
    if mc:
        ctx_lines.append("【主角】")
        ctx_lines.append(f"- id: {mc.get('character_id')}  名称: {mc.get('name') or '未知'}")
        if mc.get("ability_tier"):
            ctx_lines.append(f"- 能力: {mc.get('ability_tier')}")
        if mc.get("economy_summary"):
            ctx_lines.append(f"- 资源: {mc.get('economy_summary')}")

    wb = context.get("worldbook") or []
    if wb:
        ctx_lines.append("\n【世界书（节选）】")
        for it in wb:
            cat = f"[{it.get('category')}] " if it.get("category") else ""
            ctx_lines.append(f"- {cat}{it.get('title')}: {it.get('content')}")

    dungeon = context.get("dungeon")
    if dungeon:
        ctx_lines.append("\n【副本】")
        ctx_lines.append(f"- 副本: {dungeon.get('name') or '未命名'}")
        if dungeon.get("node_name"):
            ctx_lines.append(f"- 节点: {dungeon.get('node_name')} 进度: {dungeon.get('progress_hint')}")

    if history:
        ctx_lines.append("\n【近期剧情（节选）】")
        for i, h in enumerate(history[-6:], 1):
            ctx_lines.append(f"({i}) {h[-1200:]}")

    ctx_text = "\n".join(ctx_lines).strip()

    messages: List[Dict[str, Any]] = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})

    if ctx_text:
        messages.append({"role": "system", "content": "以下是当前故事运行时上下文：\n" + ctx_text})

    messages.append({"role": "user", "content": user_input})
    return messages


def generate_story_text(
    db: Session,
    session_id: str,
    user_input: str,
    force_stream: Optional[bool] = None,
) -> Tuple[str, GenerateMeta, Optional[Generator[str, None, None]]]:
    """返回 (full_text, meta, stream_gen)

    - 如果 stream_gen 不为空：full_text=""，由调用方边读边拼
    """
    t0 = perf_counter()

    st = _get_or_create_session_state(db, session_id)

    preset = storage.get_active_preset(db)
    system_prompt = prompts.compile_system_prompt(preset)

    llm_cfg = storage.get_active_llm_config(db)
    llm_active = storage.get_llm_active(db)

    context: Dict[str, Any] = {
        "main_character": _pick_main_character(db),
        "worldbook": _worldbook_snippets(db, limit=6),
        "dungeon": None,
    }

    dungeon, node = _dungeon_context(db, st)
    if dungeon:
        context["dungeon"] = {
            "id": dungeon.dungeon_id,
            "name": dungeon.name,
            "node_name": node.name if node else None,
            "progress_hint": "最小实现：未计算" if node else "未知",
        }

    history = _recent_story(db, session_id, limit=4)
    messages = _build_messages(system_prompt, context, history, user_input)

    # 若没有配置模型，则返回占位
    if not llm_cfg:
        story_text = (
            "【未配置模型】\n"
            "请先在【设置 → API 配置】里添加 base_url 与 api_key，并选择一个模型，然后再生成。\n\n"
            f"你的输入：{user_input}"
        )
        duration_ms = int((perf_counter() - t0) * 1000)
        meta = GenerateMeta(
            scene_title="占位输出",
            tags=["no_model"],
            tone="中性",
            pacing="-",
            dungeon_progress_hint=context.get("dungeon", {}).get("progress_hint"),
            dungeon_name=context.get("dungeon", {}).get("name"),
            dungeon_node_name=context.get("dungeon", {}).get("node_name"),
            main_character=context.get("main_character"),
            word_count=len(story_text),
            duration_ms=duration_ms,
        )
        return story_text, meta, None

    base_url = str(llm_cfg.get("base_url") or "")
    api_key = str(llm_cfg.get("api_key") or "")
    model = str(llm_active.get("model") or llm_cfg.get("default_model") or "")
    stream_flag = bool(llm_cfg.get("stream", True))
    if force_stream is not None:
        stream_flag = bool(force_stream)

    if not model:
        story_text = "【未选择模型】请在【设置 → API 配置】里选择一个可用模型。"
        duration_ms = int((perf_counter() - t0) * 1000)
        meta = GenerateMeta(scene_title="占位输出", tags=["no_model"], word_count=len(story_text), duration_ms=duration_ms)
        return story_text, meta, None

    try:
        full_text, gen = chat_completion(
            base_url=base_url,
            api_key=api_key,
            model=model,
            messages=messages,
            temperature=0.8,
            stream=stream_flag,
            timeout_s=120,
        )
    except LLMError as e:
        story_text = f"【模型请求失败】{e}"
        duration_ms = int((perf_counter() - t0) * 1000)
        meta = GenerateMeta(scene_title="错误", tags=["error"], word_count=len(story_text), duration_ms=duration_ms)
        return story_text, meta, None

    duration_ms = int((perf_counter() - t0) * 1000)

    meta = GenerateMeta(
        scene_title="新剧情",
        tags=["llm", preset.get("name") if preset else "preset"],
        tone="由预设决定",
        pacing="由预设决定",
        dungeon_progress_hint=context.get("dungeon", {}).get("progress_hint"),
        dungeon_name=context.get("dungeon", {}).get("name"),
        dungeon_node_name=context.get("dungeon", {}).get("node_name"),
        main_character=context.get("main_character"),
        duration_ms=duration_ms,
    )

    # stream：交给上层写入 story_segment
    if gen is not None:
        return "", meta, gen

    meta.word_count = len(full_text)
    return full_text, meta, None


def persist_story_segment(db: Session, session_id: str, story_text: str) -> int:
    """写入 StorySegment 并返回 order_index。"""
    st = _get_or_create_session_state(db, session_id)
    existing_count = db.query(models.StorySegment).filter(models.StorySegment.session_id == session_id).count()
    order_index = existing_count + 1

    seg = models.StorySegment(
        segment_id=f"{session_id}_{order_index}",
        session_id=session_id,
        order_index=order_index,
        text=story_text,
        created_at=datetime.utcnow(),
    )
    db.add(seg)

    st.total_word_count = (st.total_word_count or 0) + len(story_text)
    db.commit()

    return order_index
