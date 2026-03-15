from __future__ import annotations

from typing import Any, Dict, List

from ....core import prompts
from ...story.services.message_builder import build_messages
from ...story.services.runtime_context import character_roster_snippets, load_worldbook_runtime_state
from ...story.services.runtime_context_extra import build_session_runtime_context, recent_story, worldbook_snippets
from .branch_state import ensure_story_branch, resolve_runtime_settings, update_branch_runtime
from .ledger import load_memory_context
from .registry import SkillRegistry
from .strength import normalize_strength, strength_profile


def create_registry() -> SkillRegistry:
    return SkillRegistry().register("bind_session", _bind_session).register("load_history", _load_history).register("load_memory", _load_memory).register("load_characters", _load_characters).register("load_worldbook", _load_worldbook).register("plan_turn", _plan_turn)


def _bind_session(state: Dict[str, Any]) -> Dict[str, Any]:
    db, log = state["db"], state["log"]
    session_state, story, branch, global_state = ensure_story_branch(db, state["session_id"], state["user_id"])
    runtime = resolve_runtime_settings(db, session_state, branch, global_state, state.get("reasoning_strength"), state["user_id"])
    runtime["reasoning_strength"] = normalize_strength(runtime.get("reasoning_strength"))
    log.strength = runtime["reasoning_strength"]
    update_branch_runtime(db, branch, runtime)
    session_runtime = build_session_runtime_context(db, state["session_id"], user_id=state["user_id"])
    state.update({"session_state": session_state, "story": story, "branch": branch, "global_state": global_state, "runtime": runtime, "session_runtime": session_runtime, "profile": strength_profile(runtime["reasoning_strength"])})
    log.bind(storyId=story.story_id, storyTitle=story.title, branchId=branch.branch_id, sessionId=state["session_id"], presetId=(runtime.get("preset") or {}).get("id"), llmConfigId=(runtime.get("llm_cfg") or {}).get("id"), model=runtime.get("model"))
    log.add("skill", "bind_session", "Bound session, story, branch, preset and model", {"story_id": story.story_id, "story_title": story.title, "branch_id": branch.branch_id, "reasoning_strength": runtime["reasoning_strength"]}, public_label="读取会话状态", public_detail=f"故事 {story.title}，分支 {branch.branch_type}，强度 {runtime['reasoning_strength']}")
    return state


def _load_history(state: Dict[str, Any]) -> Dict[str, Any]:
    limit = int(state["profile"]["history_limit"])
    history = recent_story(state["db"], state["session_id"], user_id=state["user_id"], limit=limit)
    state["recent_history"] = history
    previews = [item[-160:] for item in history[-4:]]
    state["log"].add("skill", "load_history", "Loaded recent story context", {"history_count": len(history), "history_limit": limit, "previews": previews}, public_label="读取历史剧情", public_detail=f"载入 {len(history)} 段最近剧情")
    return state


def _load_memory(state: Dict[str, Any]) -> Dict[str, Any]:
    profile = state["profile"]
    events, variables = load_memory_context(state["db"], state["story"].story_id, state["session_id"], state["user_id"], int(profile["event_limit"]), int(profile["variable_limit"]))
    state["memory_events"] = events
    state["memory_variables"] = variables
    state["log"].add("skill", "load_memory", "Loaded structured events and variable snapshots", {"event_count": len(events), "variable_count": len(variables), "events": events, "variables": variables}, public_label="读取事件账本", public_detail=f"读取 {len(events)} 条事件，{len(variables)} 个状态变量")
    return state


def _load_characters(state: Dict[str, Any]) -> Dict[str, Any]:
    session_runtime, profile = state["session_runtime"], state["profile"]
    main_character = session_runtime.get("main_character")
    characters = character_roster_snippets(state["db"], session_id=state["session_id"], user_id=state["user_id"], limit=int(profile["character_limit"]), context_text=state["user_input"], exclude_character_id=(main_character or {}).get("character_id"))
    state.setdefault("context", {})["main_character"] = main_character
    state["context"]["characters"] = characters
    state["context"]["dungeon"] = session_runtime.get("dungeon")
    state["log"].add("skill", "load_characters", "Resolved relevant characters and player anchor", {"main_character": main_character, "characters": [_character_snapshot(item) for item in characters]}, public_label="分析相关角色", public_detail=f"识别主角与 {len(characters)} 个相关角色")
    return state


def _load_worldbook(state: Dict[str, Any]) -> Dict[str, Any]:
    active_worldbook_id, category_switches = load_worldbook_runtime_state(state["db"], state["user_id"])
    rag_context = " ".join([item[-500:] for item in state.get("recent_history", [])]) + f" {state['user_input']}"
    entries = worldbook_snippets(state["db"], user_id=state["user_id"], context_text=rag_context, limit=int(state["profile"]["worldbook_limit"]), active_worldbook_id=active_worldbook_id, category_switches=category_switches)
    state.setdefault("context", {})["worldbook"] = entries
    state["log"].add("skill", "load_worldbook", "Retrieved worldbook knowledge", {"active_worldbook_id": active_worldbook_id, "entries": [_worldbook_snapshot(item) for item in entries]}, public_label="读取世界书", public_detail=f"命中 {len(entries)} 条世界设定")
    return state


def _plan_turn(state: Dict[str, Any]) -> Dict[str, Any]:
    intent = _classify_intent(state["user_input"])
    notes: List[str] = [f"Intent: {intent}", f"Strength: {state['runtime']['reasoning_strength']}", f"Dynamic follow-up retrieval: {'enabled' if state['profile']['allow_followup'] else 'disabled'}"]
    if state.get("memory_events"):
        notes.append(f"Recent event focus: {state['memory_events'][-1]['title']}")
    state["plan_notes"] = "\n".join(notes)
    system_prompt = prompts.compile_system_prompt(state["runtime"].get("preset"))
    messages = build_messages(system_prompt, state.get("context", {}), state.get("recent_history", []), state["user_input"], memory_events=state.get("memory_events", []), memory_variables=state.get("memory_variables", []), agent_plan=state["plan_notes"])
    state["system_prompt"] = system_prompt
    state["messages"] = messages
    state["log"].set_section("retrievals", _retrieval_payload(state))
    state["log"].set_section("contextPackage", _context_package(state))
    state["log"].set_section("messagePackage", {"messageCount": len(messages), "messages": messages, "fullPrompt": "\n\n".join([f"[{item['role']}]\n{item['content']}" for item in messages])})
    state["log"].add("analysis", "plan_turn", state["plan_notes"], {"message_count": len(messages), "intent": intent}, public_label="规划本轮生成", public_detail=f"识别为 {intent}，整理上下文后生成")
    return state


def _retrieval_payload(state: Dict[str, Any]) -> Dict[str, Any]:
    return {"history": [item[-180:] for item in state.get("recent_history", [])], "events": state.get("memory_events", []), "variables": state.get("memory_variables", []), "characters": [_character_snapshot(item) for item in state.get("context", {}).get("characters", [])], "worldbook": [_worldbook_snapshot(item) for item in state.get("context", {}).get("worldbook", [])], "script": [], "substories": []}


def _context_package(state: Dict[str, Any]) -> Dict[str, Any]:
    context = state.get("context", {})
    return {"mainCharacter": context.get("main_character"), "charactersUsed": [_character_snapshot(item) for item in context.get("characters", [])], "worldbookUsed": [_worldbook_snapshot(item) for item in context.get("worldbook", [])], "dungeon": context.get("dungeon"), "planNotes": state.get("plan_notes"), "reasoningStrength": state["runtime"]["reasoning_strength"]}


def _character_snapshot(item: Dict[str, Any]) -> Dict[str, Any]:
    return {"character_id": item.get("character_id"), "name": item.get("name"), "ability_tier": item.get("ability_tier"), "economy_summary": item.get("economy_summary")}


def _worldbook_snapshot(item: Dict[str, Any]) -> Dict[str, Any]:
    return {"entry_id": item.get("entry_id"), "title": item.get("title"), "category": item.get("category"), "content": str(item.get("content") or "")[:240]}


def _classify_intent(user_input: str) -> str:
    text = str(user_input or "")
    if any(word in text for word in ["攻击", "战斗", "出手", "杀", "防御"]):
        return "combat"
    if any(word in text for word in ["调查", "寻找", "探索", "查看", "搜"]):
        return "exploration"
    if any(word in text for word in ["交谈", "询问", "说", "聊天"]):
        return "dialogue"
    return "general"
