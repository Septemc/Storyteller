from __future__ import annotations

from typing import Dict


DEFAULT_STRENGTH = "low"

STRENGTH_PROFILES: Dict[str, Dict[str, int | bool]] = {
    "low": {"history_limit": 4, "character_limit": 4, "worldbook_limit": 4, "event_limit": 4, "variable_limit": 6, "allow_followup": False},
    "medium": {"history_limit": 6, "character_limit": 6, "worldbook_limit": 6, "event_limit": 6, "variable_limit": 8, "allow_followup": True},
    "high": {"history_limit": 8, "character_limit": 8, "worldbook_limit": 8, "event_limit": 8, "variable_limit": 10, "allow_followup": True},
    "ultra": {"history_limit": 10, "character_limit": 10, "worldbook_limit": 10, "event_limit": 10, "variable_limit": 12, "allow_followup": True},
}


def normalize_strength(value: str | None) -> str:
    normalized = str(value or DEFAULT_STRENGTH).strip().lower()
    return normalized if normalized in STRENGTH_PROFILES else DEFAULT_STRENGTH


def strength_profile(value: str | None) -> Dict[str, int | bool]:
    return STRENGTH_PROFILES[normalize_strength(value)]
