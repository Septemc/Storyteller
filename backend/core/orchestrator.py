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


def _character_profile_from_row(row: models.Character) -> Dict[str, Any]:
    basic = _safe_json_loads(row.basic_json, {})
    data = _safe_json_loads(row.data_json, {})

    # 兼容 data_json 中的 tab_basic/basic，以及扁平结构（f_name 等）
    if isinstance(data, dict):
        data_basic = data.get("tab_basic") or data.get("basic")
        if isinstance(data_basic, dict):
            basic = data_basic

        # 若 data_json 是扁平结构，把根字段并入 basic，避免姓名等丢失
        flat_basic = {
            k: v
            for k, v in data.items()
            if not k.startswith("tab_") and k not in {"character_id", "type", "template_id"}
        }
        if isinstance(flat_basic, dict) and flat_basic:
            merged = dict(flat_basic)
            merged.update(basic if isinstance(basic, dict) else {})
            basic = merged

    if not isinstance(basic, dict):
        basic = {}

    def _first_non_empty(keys: List[str]) -> Optional[Any]:
        for key in keys:
            value = basic.get(key)
            if value is not None and str(value).strip() != "":
                return value
        return None

    name = _first_non_empty([
        "name", "姓名", "角色名", "f_name", "f_nickname", "昵称"
    ])
    ability_tier = _first_non_empty([
        "ability_tier", "能力评级", "境界", "f_ability_tier", "f_level", "f_realm", "f_stage"
    ])
    economy_summary = _first_non_empty([
        "economy_summary", "经济", "资源", "f_economy", "f_resources", "f_money", "f_wealth"
    ])

    return {
        "character_id": row.character_id,
        "name": name,
        "ability_tier": ability_tier,
        "economy_summary": economy_summary,
        "raw_basic": basic,
    }


def _pick_main_character(
    db: Session,
    preferred_character_id: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    """优先使用会话指定主角，其次 type=pc/player，最后取第一条。"""
    row: Optional[models.Character] = None

    if preferred_character_id:
        row = (
            db.query(models.Character)
            .filter(models.Character.character_id == preferred_character_id)
            .first()
        )

    if not row:
        row = (
            db.query(models.Character)
            .filter(models.Character.type.in_(["pc", "player", "protagonist", "main", "hero"]))
            .first()
        )
    if not row:
        row = db.query(models.Character).first()
    if not row:
        return None

    return _character_profile_from_row(row)


def _character_brief(profile: Dict[str, Any], max_len: int = 120) -> str:
    raw = profile.get("raw_basic") if isinstance(profile, dict) else {}
    if not isinstance(raw, dict):
        raw = {}

    parts: List[str] = []
    occ = raw.get("f_occ") or raw.get("occupation") or raw.get("职业")
    fac = raw.get("f_fac") or raw.get("f_faction") or raw.get("势力")
    tags = raw.get("f_tags") or raw.get("tags")

    if occ:
        parts.append(f"职业:{occ}")
    if fac:
        parts.append(f"势力:{fac}")
    if isinstance(tags, list) and tags:
        parts.append("标签:" + ",".join(str(t) for t in tags[:3]))

    text = "；".join(parts)
    if len(text) > max_len:
        return text[: max_len - 1] + "…"
    return text


def _character_roster_snippets(
    db: Session,
    limit: int = 5,
    context_text: Optional[str] = None,
    exclude_character_id: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """获取角色库摘要。

    - 优先返回被用户输入命中的角色（按姓名或 ID）
    - 其次返回其余角色，供“某某是谁”类问答使用
    """
    import re

    rows = db.query(models.Character).all()
    if not rows:
        return []

    query = (context_text or "").strip()
    tokens = re.findall(r"[A-Za-z0-9_]{2,}|[\u4e00-\u9fff]{2,}", query)

    scored: List[Tuple[int, Dict[str, Any]]] = []
    for row in rows:
        profile = _character_profile_from_row(row)
        cid = str(profile.get("character_id") or "")
        if exclude_character_id and cid == str(exclude_character_id):
            continue

        name = str(profile.get("name") or "")
        raw_basic = profile.get("raw_basic") if isinstance(profile.get("raw_basic"), dict) else {}
        search_blob = " ".join([
            cid,
            name,
            json.dumps(raw_basic, ensure_ascii=False),
        ])

        score = 0
        if query:
            if name and name in query:
                score += 100
            if cid and cid in query:
                score += 80
            for tk in tokens:
                if tk and tk in search_blob:
                    score += 3

        scored.append((score, profile))

    scored.sort(key=lambda x: x[0], reverse=True)

    selected = [p for _, p in scored[:limit]]
    return selected


def _worldbook_snippets(db: Session, limit: int = 8, context_text: Optional[str] = None) -> List[Dict[str, Any]]:
    """获取世界书片段（支持 RAG 语义检索）
    
    Args:
        db: 数据库会话
        limit: 返回数量
        context_text: 可选的上下文文本，用于语义检索。如果为 None，则退化为按重要性排序
    
    Returns:
        世界书片段列表
    """
    # 如果提供了上下文，使用 RAG 语义检索
    if context_text:
        try:
            from .rag import create_retriever
            retriever = create_retriever(db)
            results = retriever.retrieve_for_story(context_text, top_k=limit, use_hybrid=True)
            return results
        except Exception as e:
            # RAG 失败时降级到传统方式
            print(f"[Orchestrator] RAG 检索失败，降级到传统方式：{e}")
    
    # 传统方式：按重要性和更新时间排序
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


def build_session_runtime_context(db: Session, session_id: str) -> Dict[str, Any]:
    """统一构建会话上下文，供 story route 与生成器复用。"""
    st = _get_or_create_session_state(db, session_id)
    global_state = _safe_json_loads(st.global_state_json, {})
    preferred_character_id = global_state.get("main_character_id")

    main_character = _pick_main_character(db, preferred_character_id=preferred_character_id)
    dungeon, node = _dungeon_context(db, st)

    dungeon_ctx = None
    if dungeon:
        dungeon_ctx = {
            "id": dungeon.dungeon_id,
            "name": dungeon.name,
            "node_name": node.name if node else None,
            "progress_hint": _build_dungeon_progress_hint(dungeon, node),
        }

    return {
        "session_state": st,
        "global_state": global_state,
        "main_character": main_character,
        "dungeon": dungeon_ctx,
    }


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

    roster = context.get("characters") or []
    if roster:
        ctx_lines.append("\n【角色库（节选）】")
        for ch in roster:
            brief = _character_brief(ch)
            line = f"- id: {ch.get('character_id')}  名称: {ch.get('name') or '未知'}"
            if ch.get("ability_tier"):
                line += f"  境界: {ch.get('ability_tier')}"
            if brief:
                line += f"  信息: {brief}"
            ctx_lines.append(line)

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
) -> Tuple[str, GenerateMeta, Optional[Generator[str, None, None]], Dict[str, Any]]:
    """返回 (full_text, meta, stream_gen, dev_log_info)

    - 如果 stream_gen 不为空：full_text=""，由调用方边读边拼
    - dev_log_info 包含开发者日志所需的所有信息
    """
    t0 = perf_counter()
    
    dev_log_info: Dict[str, Any] = {
        "userInput": user_input,
        "fullPrompt": ""
    }

    runtime_context = build_session_runtime_context(db, session_id)
    st = runtime_context["session_state"]

    preset = storage.get_active_preset(db)
    system_prompt = prompts.compile_system_prompt(preset)

    llm_cfg = storage.get_active_llm_config(db)
    llm_active = storage.get_llm_active(db)

    # 构建用于 RAG 检索的上下文文本（从最近剧情提取关键词）
    recent_history = _recent_story(db, session_id, limit=4)
    rag_context = " ".join([h[-500:] for h in recent_history])  # 取每条最近 500 字
    if user_input:
        rag_context += " " + user_input
    
    context: Dict[str, Any] = {
        "main_character": runtime_context.get("main_character"),
        "characters": _character_roster_snippets(
            db,
            limit=6,
            context_text=user_input,
            exclude_character_id=(runtime_context.get("main_character") or {}).get("character_id") if runtime_context.get("main_character") else None,
        ),
        "worldbook": _worldbook_snippets(db, limit=6, context_text=rag_context),
        "dungeon": runtime_context.get("dungeon"),
    }

    history = _recent_story(db, session_id, limit=4)
    messages = _build_messages(system_prompt, context, history, user_input)
    
    # 构建发送给AI的完整文本用于开发者日志
    full_prompt_parts = []
    if system_prompt:
        full_prompt_parts.append(f"[System]\n{system_prompt}")
    
    # 添加上下文
    ctx_lines = []
    mc = context.get("main_character")
    if mc:
        ctx_lines.append(f"【主角】\n- id: {mc.get('character_id')}  名称: {mc.get('name') or '未知'}")
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

    roster = context.get("characters") or []
    if roster:
        ctx_lines.append("\n【角色库（节选）】")
        for ch in roster:
            brief = _character_brief(ch)
            line = f"- id: {ch.get('character_id')}  名称: {ch.get('name') or '未知'}"
            if ch.get("ability_tier"):
                line += f"  境界: {ch.get('ability_tier')}"
            if brief:
                line += f"  信息: {brief}"
            ctx_lines.append(line)
    
    dungeon_ctx = context.get("dungeon")
    if dungeon_ctx:
        ctx_lines.append("\n【剧本】")
        ctx_lines.append(f"- 剧本: {dungeon_ctx.get('name') or '未命名'}")
        if dungeon_ctx.get("node_name"):
            ctx_lines.append(f"- 节点: {dungeon_ctx.get('node_name')} 进度: {dungeon_ctx.get('progress_hint')}")
    
    if history:
        ctx_lines.append("\n【近期剧情（节选）】")
        for i, h in enumerate(history[-6:], 1):
            ctx_lines.append(f"({i}) {h[-1200:]}")
    
    if ctx_lines:
        full_prompt_parts.append("[Context]\n" + "\n".join(ctx_lines))
    
    full_prompt_parts.append(f"[User]\n{user_input}")
    dev_log_info["fullPrompt"] = "\n\n".join(full_prompt_parts)

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
        return story_text, meta, None, dev_log_info

    base_url = str(llm_cfg.get("base_url") or "")
    api_key = str(llm_cfg.get("api_key") or "")
    model = str(llm_active.get("model") or llm_cfg.get("default_model") or "")
    stream_flag = bool(llm_cfg.get("stream", True))
    if force_stream is not None:
        stream_flag = bool(force_stream)

    print(f"[ORCH_DEBUG] LLM config:")
    print(f"  base_url: {base_url[:50]}...")
    print(f"  api_key: {api_key[:15]}...")
    print(f"  llm_active: {llm_active}")
    print(f"  llm_cfg default_model: {llm_cfg.get('default_model')}")
    print(f"  final model: '{model}'")

    if not model:
        story_text = "【未选择模型】请在【设置 → API 配置】里选择一个可用模型。"
        duration_ms = int((perf_counter() - t0) * 1000)
        meta = GenerateMeta(scene_title="占位输出", tags=["no_model"], word_count=len(story_text), duration_ms=duration_ms)
        return story_text, meta, None, dev_log_info

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
        return story_text, meta, None, dev_log_info

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
        return "", meta, gen, dev_log_info

    meta.word_count = len(full_text)
    return full_text, meta, None, dev_log_info


def persist_story_segment(
    db: Session,
    session_id: str,
    story_text: str,
    user_input: str = None,
    paragraph_word_count: int = 0,
    frontend_duration: float = 0.0,
    backend_duration: float = 0.0,
) -> int:
    """写入 StorySegment 并返回 order_index。"""
    import re
    
    st = _get_or_create_session_state(db, session_id)
    existing_count = db.query(models.StorySegment).filter(models.StorySegment.session_id == session_id).count()
    order_index = existing_count + 1

    # 计算累积字数
    last_segment = (
        db.query(models.StorySegment)
        .filter(models.StorySegment.session_id == session_id)
        .order_by(models.StorySegment.order_index.desc())
        .first()
    )
    cumulative_word_count = (last_segment.cumulative_word_count if last_segment else 0) + paragraph_word_count

    # 提取各部分内容
    def extract_tag_content(text, tag_name):
        pattern = rf'<{tag_name}>(.*?)</{tag_name}>'
        match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
        if match:
            return match.group(1).strip()
        return None

    content_thinking = extract_tag_content(story_text, '思考过程')
    content_story = extract_tag_content(story_text, '正文部分')
    content_summary = extract_tag_content(story_text, '内容总结')
    content_actions = extract_tag_content(story_text, '行动选项')

    seg = models.StorySegment(
        segment_id=f"{session_id}_{order_index}",
        session_id=session_id,
        order_index=order_index,
        user_input=user_input,
        text=story_text,
        dungeon_id=st.current_dungeon_id,
        dungeon_node_id=st.current_node_id,
        paragraph_word_count=paragraph_word_count,
        cumulative_word_count=cumulative_word_count,
        frontend_duration=frontend_duration,
        backend_duration=backend_duration,
        content_thinking=content_thinking,
        content_story=content_story,
        content_summary=content_summary,
        content_actions=content_actions,
        created_at=datetime.utcnow(),
    )
    db.add(seg)

    st.total_word_count = (st.total_word_count or 0) + paragraph_word_count
    db.commit()

    return order_index
