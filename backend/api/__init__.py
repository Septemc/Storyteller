"""API package for Storyteller.

Keep package import side effects minimal. Router modules should be imported on demand.
"""

__all__ = [
    "routes_auth",
    "routes_characters",
    "routes_dungeon",
    "routes_llm",
    "routes_presets",
    "routes_regex",
    "routes_settings",
    "routes_story",
    "routes_templates",
    "routes_worldbook",
]
