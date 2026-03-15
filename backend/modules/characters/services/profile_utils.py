from __future__ import annotations

import json
from typing import Any, Dict, Iterable, Optional

SECRET_MARKERS = ["\u79d8\u5bc6", "\u9690\u85cf", "\u4e0d\u4e3a\u4eba\u77e5", "secret", "hidden", "spoiler"]
INACTIVE_MARKERS = ["\u6b7b\u4ea1", "\uff08\u6b7b\u4ea1\uff09", "\uff08\u9000\u573a\uff09", "\uff08\u5931\u8e2a\uff09"]


def load_json(value: Optional[str], default: Any) -> Any:
    try:
        return json.loads(value) if value else default
    except Exception:
        return default


def dump_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False)


def unwrap_template_config(payload: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    data = payload or {}
    config = data.get("config") if isinstance(data, dict) and isinstance(data.get("config"), dict) else data
    tabs = config.get("tabs") if isinstance(config, dict) else []
    fields = config.get("fields") if isinstance(config, dict) else []
    return {"tabs": tabs if isinstance(tabs, list) else [], "fields": fields if isinstance(fields, list) else []}


def default_character_data(full_profile: Dict[str, Any], player_profile: Dict[str, Any], meta: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    return {
        "developer_mode": full_profile,
        "player_mode": player_profile,
        "meta": meta or {},
    }


def normalize_full_profile(raw: Optional[Dict[str, Any]], character_id: str, template_id: Optional[str]) -> Dict[str, Any]:
    profile = dict(raw or {})
    profile["character_id"] = profile.get("character_id") or character_id
    profile["template_id"] = profile.get("template_id") or template_id
    profile["type"] = profile.get("type") or "npc"
    return profile


def build_player_profile(full_profile: Dict[str, Any], template_payload: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    profile = {
        "character_id": full_profile.get("character_id"),
        "template_id": full_profile.get("template_id"),
        "type": full_profile.get("type"),
    }
    for field in unwrap_template_config(template_payload).get("fields", []):
        path = str(field.get("path") or "").strip()
        if not path:
            continue
        value = get_by_path(full_profile, path)
        set_by_path(profile, path, value if is_default_visible(field) and value not in (None, "") else unknown_value(field.get("type")))
    return profile


def parse_data_json(data_json: Optional[str]) -> Dict[str, Any]:
    payload = load_json(data_json, {})
    return payload if isinstance(payload, dict) else {}


def full_profile_from_data(payload: Dict[str, Any], character_id: str, template_id: Optional[str]) -> Dict[str, Any]:
    return normalize_full_profile(payload.get("developer_mode") or payload.get("full_profile") or {}, character_id, template_id)


def player_profile_from_data(payload: Dict[str, Any], character_id: str, template_id: Optional[str], template: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    player = payload.get("player_mode") or payload.get("player_profile") or {}
    if not player:
        player = build_player_profile(full_profile_from_data(payload, character_id, template_id), template)
    return normalize_full_profile(player, character_id, template_id)


def meta_from_data(payload: Dict[str, Any]) -> Dict[str, Any]:
    meta = payload.get("meta")
    return meta if isinstance(meta, dict) else {}


def get_by_path(target: Dict[str, Any], path: str) -> Any:
    current: Any = target
    for key in [item for item in str(path).split(".") if item]:
        if not isinstance(current, dict):
            return None
        current = current.get(key)
    return current


def set_by_path(target: Dict[str, Any], path: str, value: Any) -> None:
    keys = [item for item in str(path).split(".") if item]
    current = target
    for key in keys[:-1]:
        child = current.get(key)
        if not isinstance(child, dict):
            child = {}
            current[key] = child
        current = child
    if keys:
        current[keys[-1]] = value


def is_default_visible(field: Dict[str, Any]) -> bool:
    text = " ".join(str(field.get(key) or "") for key in ["tab", "label", "desc", "id"]).lower()
    return not any(marker in text for marker in SECRET_MARKERS)


def unknown_value(field_type: Optional[str]) -> Any:
    field_type = str(field_type or "text").lower()
    if field_type in {"json", "stats_panel", "relation_graph"}:
        return {"value": "\u672a\u77e5"}
    if field_type in {"object_list"}:
        return [{"value": "\u672a\u77e5"}]
    if field_type == "tags":
        return ["\u672a\u77e5"]
    return "\u672a\u77e5"


def extract_name(profile: Dict[str, Any]) -> str:
    basic = profile.get("tab_basic") if isinstance(profile.get("tab_basic"), dict) else {}
    for key in ["f_name", "name", "f_identity", "f_nickname", "nickname"]:
        value = basic.get(key)
        if value and str(value).strip():
            return str(value).strip()
    return str(profile.get("character_id") or "")


def extract_basic_summary(profile: Dict[str, Any]) -> Dict[str, Any]:
    basic = profile.get("tab_basic") if isinstance(profile.get("tab_basic"), dict) else {}
    return {
        "character_id": profile.get("character_id"),
        "name": extract_name(profile),
        "ability_tier": first_non_empty(basic, ["ability_tier", "f_ability_tier", "f_level", "f_realm", "f_tier"]),
        "economy_summary": first_non_empty(basic, ["economy_summary", "f_economy", "f_resources", "f_money", "f_wealth"]),
        "raw_basic": basic,
    }


def first_non_empty(data: Dict[str, Any], keys: Iterable[str]) -> Optional[str]:
    for key in keys:
        value = data.get(key)
        if value is not None and str(value).strip():
            return str(value).strip()
    return None


def is_inactive_name(name: str) -> bool:
    return any(marker in str(name or "") for marker in INACTIVE_MARKERS)


def apply_status_to_name(name: str, status: str) -> str:
    base = str(name or "").replace("\uff08\u6b7b\u4ea1\uff09", "").replace("\uff08\u9000\u573a\uff09", "").replace("\uff08\u5931\u8e2a\uff09", "").strip()
    return f"{base}\uff08{status}\uff09" if status and status != "active" else base
