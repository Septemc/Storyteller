"""Preset prompt tree utilities.
包含核心结构工厂、默认预设生成以及增强的递归导入逻辑。
"""

from __future__ import annotations

import uuid
from typing import Any, Dict, List, Optional

# --- 核心工厂 ---

def new_group(title: str, children: Optional[List[Dict[str, Any]]] = None, enabled: bool = True, identifier: str = None) -> Dict[str, Any]:
    return {
        "id": f"node_{uuid.uuid4().hex[:10]}",
        "identifier": identifier or f"group_{uuid.uuid4().hex[:6]}",
        "kind": "group",
        "title": title,
        "enabled": enabled,
        "children": children or [],
        "injection_order": 0
    }

def new_prompt(
        name: str,
        content: str,
        role: str = "system",
        enabled: bool = True,
        identifier: str = None,
        **kwargs
) -> Dict[str, Any]:
    return {
        "id": f"node_{uuid.uuid4().hex[:10]}",
        "kind": "prompt",
        "title": name,
        "enabled": enabled,
        "identifier": identifier or f"prompt_{uuid.uuid4().hex[:6]}",
        "role": role,
        "content": content,

        # 高级字段
        "system_prompt": kwargs.get("system_prompt", True),
        "marker": kwargs.get("marker", False),
        "injection_position": kwargs.get("injection_position", 0),
        "injection_depth": kwargs.get("injection_depth", 4),
        "injection_order": kwargs.get("injection_order", 0),
        "forbid_overrides": kwargs.get("forbid_overrides", False),
        "injection_trigger": kwargs.get("injection_trigger", []),

        "meta": kwargs.get("meta", {})
    }

def default_preset(name: str = "默认预设") -> Dict[str, Any]:
    root = new_group(
        "全局设定",
        children=[
            new_prompt(
                name="➡️Char Personality",
                content="你是一个擅长中文叙事的互动小说引擎...",
                role="system",
                identifier="charPersonality",
                injection_order=100
            ),
            new_prompt(
                name="🧭系统设定",
                content="Identity Confirmation: 你是互动式小说生成器...",
                role="system",
                identifier="sys_setting",
                injection_order=101,
                enabled=False
            )
        ],
        identifier="root_group"
    )
    return {
        "id": f"preset_{uuid.uuid4().hex[:10]}",
        "name": name,
        "version": 2,
        "root": root,
        "meta": {},
    }

# --- 增强导入逻辑 ---

def _sanitize_node(node_data: Any) -> Dict[str, Any]:
    """递归清洗节点，确保结构合法且 ID 唯一"""
    if not isinstance(node_data, dict):
        return new_group("无效节点", enabled=False)

    # 1. 确定类型
    # 如果有 children 或者是 group，则视为组
    raw_children = node_data.get("children")
    is_group = node_data.get("kind") == "group" or isinstance(raw_children, list)

    # 2. 提取基础属性
    title = node_data.get("title") or node_data.get("name") or "导入节点"
    enabled = node_data.get("enabled", True)
    identifier = node_data.get("identifier") # 保留原有标识符以便引用

    if is_group:
        # 递归处理子节点
        clean_children = []
        if isinstance(raw_children, list):
            for child in raw_children:
                clean_children.append(_sanitize_node(child))

        # 使用工厂创建（自动生成新 UUID）
        return new_group(title, children=clean_children, enabled=enabled, identifier=identifier)

    else:
        # Prompt 节点处理
        content = node_data.get("content") or node_data.get("text") or ""
        role = node_data.get("role", "system")

        # 提取额外参数
        extra = {
            "system_prompt": node_data.get("system_prompt", True),
            "marker": node_data.get("marker", False),
            "injection_position": node_data.get("injection_position", 0),
            "injection_depth": node_data.get("injection_depth", 4),
            "injection_order": node_data.get("injection_order", 0),
            "forbid_overrides": node_data.get("forbid_overrides", False),
            "injection_trigger": node_data.get("injection_trigger", []),
            "meta": node_data.get("meta", {})
        }

        return new_prompt(title, content, role, enabled, identifier, **extra)


def import_preset(payload: Any, name_hint: str = "导入预设") -> Dict[str, Any]:
    """
    通用导入入口。
    支持：
    1. 完整 Preset 导出 (包含 root)
    2. 单个 Root Node 对象
    3. Prompts 列表 (扁平结构)
    """
    print("[INFO]:导入预设按钮成功调用了prompt.py中的import_preset函数!")
    clean_root = None

    # Case A: 已经是完整 Preset 结构
    if isinstance(payload, dict) and "root" in payload:
        # 从 root 开始清洗
        clean_root = _sanitize_node(payload["root"])

    # Case B: 只是一个 Root Node (Dict)
    elif isinstance(payload, dict) and ("children" in payload or payload.get("kind") == "group"):
        clean_root = _sanitize_node(payload)

    # Case C: 列表 (List of prompts)
    elif isinstance(payload, list):
        children = [_sanitize_node(item) for item in payload]
        clean_root = new_group(f"{name_hint} Root", children=children)

    # Case D: 其他 (Dict but acts like a prompt or list wrapper)
    elif isinstance(payload, dict):
        if "prompts" in payload and isinstance(payload["prompts"], list):
             children = [_sanitize_node(item) for item in payload["prompts"]]
             clean_root = new_group(f"{name_hint} Root", children=children)
        else:
             # 单个 Prompt
             clean_node = _sanitize_node(payload)
             # 如果它本身变成了 group，直接用；否则包一层
             if clean_node["kind"] == "group":
                 clean_root = clean_node
             else:
                 clean_root = new_group(f"{name_hint} Root", children=[clean_node])

    if not clean_root:
        # Fallback
        clean_root = new_group("空导入", enabled=False)

    return {
        "id": f"preset_{uuid.uuid4().hex[:10]}",
        "name": name_hint,
        "version": 1,
        "root": clean_root,
        "meta": {"source": "import"}
    }

# --- 编译逻辑 (保持不变，但为了完整性列出) ---

def _collect_leaves(node: Dict[str, Any], out: List[Dict[str, Any]]) -> None:
    if not node.get("enabled", True):
        return
    if node.get("kind") == "prompt":
        out.append(node)
        return
    for child in node.get("children", []):
        _collect_leaves(child, out)

def compile_system_prompt(preset: Optional[Dict[str, Any]]) -> str:
    if not preset or not preset.get("root"):
        return ""
    leaves = []
    _collect_leaves(preset["root"], leaves)
    leaves.sort(key=lambda x: x.get("injection_order", 0))
    chunks = []
    for node in leaves:
        content = (node.get("content") or "").strip()
        if not content: continue
        ident = node.get("identifier") or node.get("title")
        chunks.append(f"--- {ident} ---\n{content}")
    return "\n\n".join(chunks)