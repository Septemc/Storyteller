from __future__ import annotations

from typing import Any, Dict, List

from .factory import new_group, new_prompt


def sanitize_node(node_data: Any) -> Dict[str, Any]:
    if not isinstance(node_data, dict):
        return new_group("无效节点", enabled=False)
    raw_children = node_data.get("children")
    is_group = node_data.get("kind") == "group" or isinstance(raw_children, list)
    title = node_data.get("title") or node_data.get("name") or "导入节点"
    enabled = node_data.get("enabled", True)
    identifier = node_data.get("identifier")
    if is_group:
        clean_children = [sanitize_node(child) for child in raw_children or []]
        return new_group(title, children=clean_children, enabled=enabled, identifier=identifier)
    extra = {
        "system_prompt": node_data.get("system_prompt", True),
        "marker": node_data.get("marker", False),
        "injection_position": node_data.get("injection_position", 0),
        "injection_depth": node_data.get("injection_depth", 4),
        "injection_order": node_data.get("injection_order", 0),
        "forbid_overrides": node_data.get("forbid_overrides", False),
        "injection_trigger": node_data.get("injection_trigger", []),
        "meta": node_data.get("meta", {}),
    }
    return new_prompt(title, node_data.get("content") or node_data.get("text") or "", node_data.get("role", "system"), enabled, identifier, **extra)


def import_preset(payload: Any, name_hint: str = "导入预设") -> Dict[str, Any]:
    clean_root = None
    if isinstance(payload, dict) and "root" in payload:
        clean_root = sanitize_node(payload["root"])
    elif isinstance(payload, dict) and ("children" in payload or payload.get("kind") == "group"):
        clean_root = sanitize_node(payload)
    elif isinstance(payload, list):
        clean_root = new_group(f"{name_hint} Root", children=[sanitize_node(item) for item in payload])
    elif isinstance(payload, dict):
        prompts_list = payload.get("prompts")
        if isinstance(prompts_list, list):
            clean_root = new_group(f"{name_hint} Root", children=[sanitize_node(item) for item in prompts_list])
        else:
            clean_node = sanitize_node(payload)
            clean_root = clean_node if clean_node["kind"] == "group" else new_group(f"{name_hint} Root", children=[clean_node])
    if not clean_root:
        clean_root = new_group("空导入", enabled=False)
    from uuid import uuid4

    return {"id": f"preset_{uuid4().hex[:10]}", "name": name_hint, "version": 1, "root": clean_root, "meta": {"source": "import"}}


def collect_leaves(node: Dict[str, Any], out: List[Dict[str, Any]]) -> None:
    if not node.get("enabled", True):
        return
    if node.get("kind") == "prompt":
        out.append(node)
        return
    for child in node.get("children", []):
        collect_leaves(child, out)
