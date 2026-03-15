from __future__ import annotations

from typing import Any, Callable, Dict

SkillFn = Callable[[Dict[str, Any]], Dict[str, Any]]


class SkillRegistry:
    def __init__(self) -> None:
        self._skills: Dict[str, SkillFn] = {}

    def register(self, name: str, fn: SkillFn) -> "SkillRegistry":
        self._skills[name] = fn
        return self

    def execute(self, name: str, state: Dict[str, Any]) -> Dict[str, Any]:
        if name not in self._skills:
            raise KeyError(f"skill '{name}' is not registered")
        return self._skills[name](state)
