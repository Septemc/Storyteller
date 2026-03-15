from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional


class AgentDeveloperLog:
    def __init__(self, session_id: str, user_input: str, strength: str) -> None:
        self.session_id = session_id
        self.user_input = user_input
        self.strength = strength
        self.bindings: Dict[str, Any] = {}
        self.entries: List[Dict[str, Any]] = []
        self.sections: Dict[str, Any] = {}

    def bind(self, **kwargs: Any) -> None:
        self.bindings.update({key: value for key, value in kwargs.items() if value not in (None, "", [], {})})

    def add(self, kind: str, title: str, detail: str = "", data: Optional[Dict[str, Any]] = None, public_label: str = "", public_detail: str = "") -> None:
        self.entries.append(
            {
                "kind": kind,
                "title": title,
                "detail": detail,
                "data": data or {},
                "publicLabel": public_label or title,
                "publicDetail": public_detail,
                "timestamp": datetime.utcnow().isoformat(),
            }
        )

    def set_section(self, name: str, value: Any) -> None:
        self.sections[name] = value

    def payload(self) -> Dict[str, Any]:
        return {
            "version": "agent_v2",
            "sessionId": self.session_id,
            "reasoningStrength": self.strength,
            "userInput": self.user_input,
            "bindings": self.bindings,
            "entries": self.entries,
            "publicLog": self._public_log(),
            "developer": self.sections,
        }

    def _public_log(self) -> Dict[str, Any]:
        visible = []
        for entry in self.entries:
            if entry["kind"] not in {"skill", "analysis", "generation"}:
                continue
            visible.append(
                {
                    "label": entry.get("publicLabel") or entry["title"],
                    "detail": entry.get("publicDetail") or "",
                    "kind": entry["kind"],
                    "timestamp": entry["timestamp"],
                }
            )
        return {"title": "Agent Log", "steps": visible}
