from __future__ import annotations

from time import perf_counter
from typing import Any, Dict, Generator, Optional, Tuple

from sqlalchemy.orm import Session

from ....modules.agent.services import prepare_agent_turn
from .types import GenerateMeta


def generate_story_text(db: Session, session_id: str, user_input: str, force_stream: Optional[bool] = None, user_id: Optional[str] = None, reasoning_strength: Optional[str] = None) -> Tuple[str, GenerateMeta, Optional[Generator[str, None, None]], Dict[str, Any], Dict[str, Any]]:
    started = perf_counter()
    turn = prepare_agent_turn(db=db, session_id=session_id, user_input=user_input, force_stream=force_stream, user_id=user_id, reasoning_strength=reasoning_strength)
    turn.meta.duration_ms = turn.meta.duration_ms or int((perf_counter() - started) * 1000)
    return turn.text, turn.meta, turn.stream_gen, turn.dev_log_info, turn.agent_state
