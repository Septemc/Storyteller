from __future__ import annotations

import json
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional

DEFAULT_PRESET_PATH = Path(__file__).resolve().parents[5] / "data" / "default_preset.json"


def new_group(title: str, children: Optional[List[Dict[str, Any]]] = None, enabled: bool = True, identifier: str = None) -> Dict[str, Any]:
    return {
        "id": f"node_{uuid.uuid4().hex[:10]}",
        "identifier": identifier or f"group_{uuid.uuid4().hex[:6]}",
        "kind": "group",
        "title": title,
        "enabled": enabled,
        "children": children or [],
        "injection_order": 0,
    }


def new_prompt(name: str, content: str, role: str = "system", enabled: bool = True, identifier: str = None, **kwargs) -> Dict[str, Any]:
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
        "meta": kwargs.get("meta", {}),
    }


def load_preset_from_file() -> Optional[Dict[str, Any]]:
    if DEFAULT_PRESET_PATH.exists():
        return json.loads(DEFAULT_PRESET_PATH.read_text(encoding="utf-8"))
    return None


def create_minimal_preset(name: str = "最小预设") -> Dict[str, Any]:
    root = new_group(
        "基础设定",
        children=[
            new_prompt("基础角色设定", "你是一个互动小说引擎，根据用户输入生成剧情。", identifier="basic_character", injection_order=100),
            new_prompt("输出格式", "<思考过程>...</思考过程>\n<正文部分>...</正文部分>\n<内容总结>...</内容总结>\n<行动选项>...</行动选项>", identifier="output_format", injection_order=102),
        ],
        identifier="root_group",
    )
    return {"id": f"preset_{uuid.uuid4().hex[:10]}", "name": name, "version": 1, "root": root, "meta": {}}


def default_preset(name: str = "默认预设") -> Dict[str, Any]:
    preset_data = load_preset_from_file()
    if preset_data:
        preset_data = preset_data.copy()
        preset_data["id"] = f"preset_{uuid.uuid4().hex[:10]}"
        if name != "默认预设":
            preset_data["name"] = name
        return preset_data
    return create_minimal_preset(name)
