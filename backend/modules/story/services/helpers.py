from __future__ import annotations

import json
from typing import Any, Dict, List, Optional


def safe_json_loads(value: Optional[str], default: Any) -> Any:
    if not value:
        return default
    try:
        return json.loads(value)
    except Exception:
        return default


def first_non_empty(data: Dict[str, Any], keys: List[str]) -> Optional[str]:
    for key in keys:
        value = data.get(key)
        if value is None:
            continue
        text = str(value).strip()
        if text:
            return text
    return None


def settings_key(user_id: Optional[str]) -> str:
    return f"global::{user_id}" if user_id else "global::public"
