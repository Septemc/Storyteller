from __future__ import annotations

import json
import uuid
from time import perf_counter
from typing import Any, Dict, Optional

from sqlalchemy.orm import Session

from ....core.llm_client import LLMError, chat_completion
from ....db import models
from ...characters.services.dynamic_sync import sync_characters_after_turn
from ...story.services.content_parser import extract_story_parts, is_valid_story_content
from ...story.services.persistence import persist_story_segment
from ...story.services.types import GenerateMeta
from .developer_log import AgentDeveloperLog
from .ledger import persist_turn_memory
from .log_store import persist_segment_log
from .skills import create_registry
from .types import AgentTurnStart


def prepare_agent_turn(
    db: Session,
    session_id: str,
    user_input: str,
    force_stream: Optional[bool],
    user_id: Optional[str],
    reasoning_strength: Optional[str],
) -> AgentTurnStart:
    started = perf_counter()
    log = AgentDeveloperLog(session_id=session_id, user_input=user_input, strength=str(reasoning_strength or "low"))
    state: Dict[str, Any] = {
        "db": db,
        "session_id": session_id,
        "user_input": user_input,
        "user_id": user_id,
        "reasoning_strength": reasoning_strength,
        "log": log,
    }
    registry = create_registry()
    for skill_name in ["bind_session", "load_history", "load_memory", "load_characters", "load_worldbook", "plan_turn"]:
        registry.execute(skill_name, state)
    runtime = state["runtime"]
    llm_cfg = runtime.get("llm_cfg")
    model = str(runtime.get("model") or "")
    meta = _build_meta(state, started)
    if not llm_cfg:
        return AgentTurnStart(text=f"[no model config]\n\nuser_input: {user_input}", meta=meta, stream_gen=None, dev_log_info=log.payload(), agent_state=state)
    if not model:
        return AgentTurnStart(text="[no model selected]", meta=meta, stream_gen=None, dev_log_info=log.payload(), agent_state=state)
    try:
        full_text, stream_gen = chat_completion(
            base_url=str(llm_cfg.get("base_url") or ""),
            api_key=str(llm_cfg.get("api_key") or ""),
            model=model,
            messages=state["messages"],
            temperature=0.8,
            stream=bool(llm_cfg.get("stream", True)) if force_stream is None else bool(force_stream),
            timeout_s=120,
        )
    except LLMError as exc:
        log.add("error", "model_request_failed", str(exc))
        return AgentTurnStart(text=f"[model request failed] {exc}", meta=meta, stream_gen=None, dev_log_info=log.payload(), agent_state=state)
    log.add("generation", "request_model", "Dispatched model request", {"message_count": len(state["messages"]), "stream": stream_gen is not None, "model": model}, public_label="调用模型生成", public_detail=f"模型 {model} 已开始生成本轮正文")
    if stream_gen is not None:
        return AgentTurnStart(text="", meta=meta, stream_gen=stream_gen, dev_log_info=log.payload(), agent_state=state)
    full_text = full_text if is_valid_story_content(full_text) else "[empty generation]"
    meta.word_count = len(full_text)
    return AgentTurnStart(text=full_text, meta=meta, stream_gen=None, dev_log_info=log.payload(), agent_state=state)


def finalize_agent_turn(
    db: Session,
    session_id: str,
    user_input: str,
    story_text: str,
    meta: GenerateMeta,
    agent_state: Dict[str, Any],
    user_id: Optional[str],
    frontend_duration: float = 0.0,
) -> Dict[str, Any]:
    log: AgentDeveloperLog = agent_state["log"]
    parts = extract_story_parts(story_text)
    paragraph_word_count = len(parts.get("story") or story_text)
    order_index = persist_story_segment(
        db,
        session_id,
        story_text,
        user_input,
        paragraph_word_count=paragraph_word_count,
        frontend_duration=frontend_duration,
        backend_duration=float(meta.duration_ms or 0),
        user_id=user_id,
    )
    segment = db.query(models.StorySegment).filter(
        models.StorySegment.session_id == session_id,
        models.StorySegment.order_index == order_index,
    ).first()
    segment_id = segment.segment_id if segment else f"{session_id}_{order_index}"
    branch = agent_state["branch"]
    branch.last_segment_id = segment_id
    memory = persist_turn_memory(db, agent_state["story"].story_id, session_id, segment_id, user_input, story_text, user_id)
    log.add("skill", "write_memory", "Persisted story segment, event ledger and variable snapshots", {"segment_id": segment_id, "event_count": len(memory["events"]), "snapshot_count": len(memory["snapshots"]), "events": memory["events"], "snapshots": memory["snapshots"]}, public_label="写回事件与状态", public_detail=f"已写回 {len(memory['events'])} 条事件和 {len(memory['snapshots'])} 个状态快照")
    character_sync = sync_characters_after_turn(db, agent_state, segment_id, story_text, user_id)
    log.add("skill", "sync_characters", "Synchronized character cards for newly introduced or changed characters", character_sync, public_label="同步角色档案", public_detail=f"新增 {len(character_sync.get('created', []))} 个角色，更新 {len(character_sync.get('updated', []))} 个角色")
    log.set_section("writeback", {"memory": memory, "characters": character_sync})
    payload = log.payload()
    _save_run_log(db, agent_state["story"].story_id, session_id, segment_id, branch.reasoning_strength, payload, user_id)
    persist_segment_log(db, agent_state["story"].story_id, session_id, segment_id, payload, user_id)
    branch.summary_short = memory["snapshots"][0]["value"]["text"] if memory["snapshots"] else branch.summary_short
    db.commit()
    return {"segment_id": segment_id, "order_index": order_index, "dev_log_info": payload}


def _build_meta(state: Dict[str, Any], started: float) -> GenerateMeta:
    context = state.get("context", {})
    dungeon = context.get("dungeon") or {}
    return GenerateMeta(
        scene_title="New Scene",
        tags=["agent_phase1", state["runtime"]["reasoning_strength"]],
        tone="preset-driven",
        pacing="dynamic",
        dungeon_progress_hint=dungeon.get("progress_hint"),
        dungeon_name=dungeon.get("name"),
        dungeon_node_name=dungeon.get("node_name"),
        main_character=context.get("main_character"),
        duration_ms=int((perf_counter() - started) * 1000),
    )


def _save_run_log(
    db: Session,
    story_id: str,
    session_id: str,
    segment_id: str,
    strength: str,
    trace: Dict[str, Any],
    user_id: Optional[str],
) -> None:
    db.add(
        models.AgentRunLog(
            run_id=f"run_{uuid.uuid4().hex[:12]}",
            story_id=story_id,
            session_id=session_id,
            segment_id=segment_id,
            reasoning_strength=strength,
            trace_json=json.dumps(trace, ensure_ascii=False),
            user_id=user_id,
        )
    )
    db.commit()
