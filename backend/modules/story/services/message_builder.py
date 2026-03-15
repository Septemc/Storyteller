from __future__ import annotations

from typing import Any, Dict, List, Optional

from .content_parser import extract_story_parts
from .runtime_context import character_brief
from .types import OUTPUT_FORMAT_CONSTRAINT_PATH


def load_output_format_constraint() -> str:
    try:
        return OUTPUT_FORMAT_CONSTRAINT_PATH.read_text(encoding="utf-8").strip() if OUTPUT_FORMAT_CONSTRAINT_PATH.exists() else ""
    except Exception:
        return ""


def build_messages(system_prompt: str, context: Dict[str, Any], history: List[str], user_input: str, memory_events: Optional[List[Dict[str, Any]]] = None, memory_variables: Optional[List[Dict[str, Any]]] = None, agent_plan: str = "") -> List[Dict[str, str]]:
    ctx_lines: List[str] = []
    main_character = context.get("main_character")
    if main_character:
        ctx_lines.extend([f"[Main Character]\n- id: {main_character.get('character_id')}  name: {main_character.get('name') or 'unknown'}"])
        if main_character.get("ability_tier"):
            ctx_lines.append(f"- ability: {main_character.get('ability_tier')}")
        if main_character.get("economy_summary"):
            ctx_lines.append(f"- economy: {main_character.get('economy_summary')}")
    if context.get("characters"):
        ctx_lines.append("\n[Characters]")
        for character in context["characters"]:
            line = f"- id: {character.get('character_id')}  name: {character.get('name') or 'unknown'}"
            if character.get("ability_tier"):
                line += f"  realm: {character.get('ability_tier')}"
            brief = character_brief(character)
            if brief:
                line += f"  info: {brief}"
            ctx_lines.append(line)
    if context.get("worldbook"):
        ctx_lines.append("\n[Worldbook]")
        ctx_lines.extend([f"- {'[' + item.get('category') + '] ' if item.get('category') else ''}{item.get('title')}: {item.get('content')}" for item in context["worldbook"]])
    if context.get("dungeon"):
        dungeon = context["dungeon"]
        ctx_lines.extend([f"\n[Scenario]\n- name: {dungeon.get('name') or 'unknown'}"])
        if dungeon.get("node_name"):
            ctx_lines.append(f"- node: {dungeon.get('node_name')}  progress: {dungeon.get('progress_hint')}")
    if history:
        history_items = [_history_body(item) for item in history]
        history_items = [item for item in history_items if item]
        ctx_lines.append("\n[Recent Story]")
        ctx_lines.extend([f"({idx}) {item[-1200:]}" for idx, item in enumerate(history_items[-6:], 1)])
    if memory_events:
        ctx_lines.append("\n[Structured Events]")
        ctx_lines.extend([f"- {item.get('event_type')}: {item.get('title')}" for item in memory_events[:6]])
    if memory_variables:
        ctx_lines.append("\n[Variable Snapshots]")
        ctx_lines.extend([f"- {item.get('namespace')}::{item.get('key')}: {item.get('value')}" for item in memory_variables[:8]])
    messages = [{"role": "system", "content": system_prompt}] if system_prompt else []
    if ctx_lines:
        messages.append({"role": "system", "content": "Current story runtime context:\n" + "\n".join(ctx_lines)})
    if agent_plan:
        messages.append({"role": "system", "content": "Turn plan:\n" + agent_plan})
    constraint = load_output_format_constraint()
    if constraint:
        messages.append({"role": "system", "content": constraint})
    messages.append({"role": "user", "content": user_input})
    return messages


def build_dev_log_info(user_input: str, system_prompt: str, context: Dict[str, Any], history: List[str], messages: List[Dict[str, str]]) -> Dict[str, Any]:
    return {"userInput": user_input, "systemPrompt": system_prompt, "contextInfo": context, "historyInfo": history[-6:], "messages": messages, "fullPrompt": "\n\n".join([f"[{message['role']}]\n{message['content']}" for message in messages])}


def _history_body(text: str) -> str:
    parts = extract_story_parts(text or "")
    if parts.get("story"):
        return parts["story"].strip()
    return (text or "").strip()
