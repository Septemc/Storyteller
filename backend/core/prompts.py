"""Preset prompt tree utilities.
包含核心结构工厂、默认预设生成以及增强的递归导入逻辑。

重构说明：
不再使用硬编码的备用预设，完全依赖数据库或JSON文件。
"""

from __future__ import annotations

import json
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional

DEFAULT_PRESET_PATH = Path(__file__).parent.parent.parent / "data" / "default_preset.json"


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

        "system_prompt": kwargs.get("system_prompt", True),
        "marker": kwargs.get("marker", False),
        "injection_position": kwargs.get("injection_position", 0),
        "injection_depth": kwargs.get("injection_depth", 4),
        "injection_order": kwargs.get("injection_order", 0),
        "forbid_overrides": kwargs.get("forbid_overrides", False),
        "injection_trigger": kwargs.get("injection_trigger", []),

        "meta": kwargs.get("meta", {})
    }


def load_preset_from_file() -> Optional[Dict[str, Any]]:
    """从JSON文件加载预设配置"""
    if DEFAULT_PRESET_PATH.exists():
        with open(DEFAULT_PRESET_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return None


def create_minimal_preset(name: str = "最小预设") -> Dict[str, Any]:
    """创建最小化的预设配置（仅作为最后的备用方案）"""
    root = new_group(
        "基础设定",
        children=[
            new_prompt(
                name="基础角色设定",
                content="你是一个互动小说引擎，根据用户输入生成剧情。",
                role="system",
                identifier="basic_character",
                injection_order=100
            ),
            new_prompt(
                name="输出格式",
                content="""
请严格按照以下XML格式输出内容：

<思考过程>
思考当前行动的正文输出大纲。
</思考过程>

<正文部分>
输出剧情内容，字数控制在200-500字。
</正文部分>

<内容总结>
总结本次输出的正文内容。
</内容总结>

<行动选项>
1: 第一个行动选项
2: 第二个行动选项
3: 第三个行动选项
</行动选项>
                """,
                role="system",
                identifier="output_format",
                injection_order=102
            )
        ],
        identifier="root_group"
    )
    return {
        "id": f"preset_{uuid.uuid4().hex[:10]}",
        "name": name,
        "version": 1,
        "root": root,
        "meta": {},
    }


def default_preset(name: str = "默认预设") -> Dict[str, Any]:
    """获取默认预设配置，优先从JSON文件加载"""
    preset_data = load_preset_from_file()
    
    if preset_data:
        preset_data = preset_data.copy()
        preset_data["id"] = f"preset_{uuid.uuid4().hex[:10]}"
        if name != "默认预设":
            preset_data["name"] = name
        return preset_data
    
    return create_minimal_preset(name)


def _sanitize_node(node_data: Any) -> Dict[str, Any]:
    """递归清洗节点，确保结构合法且 ID 唯一"""
    if not isinstance(node_data, dict):
        return new_group("无效节点", enabled=False)

    raw_children = node_data.get("children")
    is_group = node_data.get("kind") == "group" or isinstance(raw_children, list)

    title = node_data.get("title") or node_data.get("name") or "导入节点"
    enabled = node_data.get("enabled", True)
    identifier = node_data.get("identifier")

    if is_group:
        clean_children = []
        if isinstance(raw_children, list):
            for child in raw_children:
                clean_children.append(_sanitize_node(child))
        return new_group(title, children=clean_children, enabled=enabled, identifier=identifier)

    else:
        content = node_data.get("content") or node_data.get("text") or ""
        role = node_data.get("role", "system")

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

    if isinstance(payload, dict) and "root" in payload:
        clean_root = _sanitize_node(payload["root"])

    elif isinstance(payload, dict) and ("children" in payload or payload.get("kind") == "group"):
        clean_root = _sanitize_node(payload)

    elif isinstance(payload, list):
        children = [_sanitize_node(item) for item in payload]
        clean_root = new_group(f"{name_hint} Root", children=children)

    elif isinstance(payload, dict):
        if "prompts" in payload and isinstance(payload["prompts"], list):
             children = [_sanitize_node(item) for item in payload["prompts"]]
             clean_root = new_group(f"{name_hint} Root", children=children)
        else:
             clean_node = _sanitize_node(payload)
             if clean_node["kind"] == "group":
                 clean_root = clean_node
             else:
                 clean_root = new_group(f"{name_hint} Root", children=[clean_node])

    if not clean_root:
        clean_root = new_group("空导入", enabled=False)

    return {
        "id": f"preset_{uuid.uuid4().hex[:10]}",
        "name": name_hint,
        "version": 1,
        "root": clean_root,
        "meta": {"source": "import"}
    }


def _collect_leaves(node: Dict[str, Any], out: List[Dict[str, Any]]) -> None:
    if not node.get("enabled", True):
        return
    if node.get("kind") == "prompt":
        out.append(node)
        return
    for child in node.get("children", []):
        _collect_leaves(child, out)


def compile_system_prompt(preset: Optional[Dict[str, Any]]) -> str:
    """编译预设为系统提示词字符串"""
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


def compile_system_prompt_with_details(preset: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """编译预设为系统提示词，同时返回详细信息用于开发者日志"""
    if not preset or not preset.get("root"):
        return {"prompt": "", "prompts_used": []}
    
    leaves = []
    _collect_leaves(preset["root"], leaves)
    leaves.sort(key=lambda x: x.get("injection_order", 0))
    
    prompts_used = []
    chunks = []
    
    for node in leaves:
        content = (node.get("content") or "").strip()
        if not content: continue
        
        ident = node.get("identifier") or node.get("title")
        chunks.append(f"--- {ident} ---\n{content}")
        
        prompts_used.append({
            "identifier": ident,
            "title": node.get("title", "未命名"),
            "enabled": node.get("enabled", True),
            "injection_order": node.get("injection_order", 0),
            "content_length": len(content)
        })
    
    return {
        "prompt": "\n\n".join(chunks),
        "prompts_used": prompts_used,
        "preset_name": preset.get("name", "未命名"),
        "preset_id": preset.get("id", "")
    }
