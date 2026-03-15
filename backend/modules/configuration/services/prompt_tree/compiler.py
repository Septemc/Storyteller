from __future__ import annotations

from typing import Any, Dict, List, Optional

from .importer import collect_leaves


def compile_system_prompt(preset: Optional[Dict[str, Any]]) -> str:
    if not preset or not preset.get("root"):
        return ""
    leaves: List[Dict[str, Any]] = []
    collect_leaves(preset["root"], leaves)
    leaves.sort(key=lambda item: item.get("injection_order", 0))
    chunks = []
    for node in leaves:
        content = (node.get("content") or "").strip()
        if content:
            ident = node.get("identifier") or node.get("title")
            chunks.append(f"--- {ident} ---\n{content}")
    return "\n\n".join(chunks)


def compile_system_prompt_with_details(preset: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    if not preset or not preset.get("root"):
        return {"prompt": "", "prompts_used": []}
    leaves: List[Dict[str, Any]] = []
    collect_leaves(preset["root"], leaves)
    leaves.sort(key=lambda item: item.get("injection_order", 0))
    chunks: List[str] = []
    prompts_used: List[Dict[str, Any]] = []
    for node in leaves:
        content = (node.get("content") or "").strip()
        if not content:
            continue
        ident = node.get("identifier") or node.get("title")
        chunks.append(f"--- {ident} ---\n{content}")
        prompts_used.append(
            {
                "identifier": ident,
                "title": node.get("title", "未命名"),
                "enabled": node.get("enabled", True),
                "injection_order": node.get("injection_order", 0),
                "content_length": len(content),
            }
        )
    return {
        "prompt": "\n\n".join(chunks),
        "prompts_used": prompts_used,
        "preset_name": preset.get("name", "未命名"),
        "preset_id": preset.get("id", ""),
    }
