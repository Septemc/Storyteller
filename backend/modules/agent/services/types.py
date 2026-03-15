from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Generator, Optional

from ...story.services.types import GenerateMeta


@dataclass
class AgentTurnStart:
    text: str
    meta: GenerateMeta
    stream_gen: Optional[Generator[str, None, None]]
    dev_log_info: Dict[str, Any]
    agent_state: Dict[str, Any]
