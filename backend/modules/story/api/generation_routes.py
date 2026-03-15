from __future__ import annotations

from typing import Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from ....core import orchestrator
from ....core.auth import User as AuthUser, get_current_user_sync
from ....core.session_state import SessionStateConflictError
from ....core.tenant import current_user_id, owner_only
from ....db import models
from ....db.base import get_db
from .schemas import StoryGenerateRequest, StoryGenerateResponse, StoryMeta

router = APIRouter()


@router.post("/story/generate", response_model=StoryGenerateResponse)
def generate_story(req: StoryGenerateRequest, db: Session = Depends(get_db), current_user: Optional[AuthUser] = Depends(get_current_user_sync)) -> StoryGenerateResponse:
    user_id = current_user_id(current_user)
    try:
        story_text, meta_obj, gen, _, agent_state = orchestrator.generate_story_text(db=db, session_id=req.session_id, user_input=req.user_input, force_stream=False, user_id=user_id, reasoning_strength=req.reasoning_strength)
    except SessionStateConflictError as exc:
        raise HTTPException(status_code=409, detail="session belongs to another user scope") from exc
    if gen is not None:
        story_text = "".join(list(gen))
    if not orchestrator.is_valid_story_content(story_text):
        raise HTTPException(status_code=400, detail="AI returned empty content")
    finalize_info = orchestrator.finalize_agent_turn(db, req.session_id, req.user_input, story_text, meta_obj, agent_state, user_id=user_id, frontend_duration=req.frontend_duration or 0.0)
    segment = owner_only(db.query(models.StorySegment).filter(models.StorySegment.segment_id == finalize_info["segment_id"]), models.StorySegment, user_id).first()
    meta = StoryMeta(**(meta_obj.__dict__ if hasattr(meta_obj, "__dict__") else dict(meta_obj)))
    meta.word_count = len((segment.content_story if segment else "") or "")
    return StoryGenerateResponse(story=story_text, meta=meta, segment_id=segment.segment_id if segment else finalize_info["segment_id"], dev_log_info=finalize_info["dev_log_info"])


@router.post("/story/generate_stream")
def generate_story_stream(req: StoryGenerateRequest, db: Session = Depends(get_db), current_user: Optional[AuthUser] = Depends(get_current_user_sync)):
    user_id = current_user_id(current_user)

    def sse(event: str, data_obj: Dict) -> str:
        import json

        return f"event: {event}\ndata: {json.dumps(data_obj, ensure_ascii=False)}\n\n"

    def stream():
        story_buf: List[str] = []
        try:
            full_text, meta_obj, stream_gen, dev_log_info, agent_state = orchestrator.generate_story_text(db=db, session_id=req.session_id, user_input=req.user_input, force_stream=True, user_id=user_id, reasoning_strength=req.reasoning_strength)
            meta_dict = meta_obj.__dict__ if hasattr(meta_obj, "__dict__") else dict(meta_obj)
            meta_dict.setdefault("duration_ms", 0)
            if dev_log_info:
                yield sse("dev_log", dev_log_info)
            yield sse("meta", meta_dict)
            if stream_gen is None:
                story_buf.append(full_text)
                if full_text:
                    yield sse("delta", {"text": full_text})
            else:
                for delta in stream_gen:
                    story_buf.append(delta)
                    yield sse("delta", {"text": delta})
            final_text = "".join(story_buf)
            if not orchestrator.is_valid_story_content(final_text):
                yield sse("empty", {"message": "AI returned empty content"})
                return
            finalize_info = orchestrator.finalize_agent_turn(db, req.session_id, req.user_input, final_text, meta_obj, agent_state, user_id=user_id, frontend_duration=req.frontend_duration or 0.0)
            yield sse("dev_log", finalize_info["dev_log_info"])
            yield sse("done", {})
        except SessionStateConflictError:
            yield sse("error", {"message": "session belongs to another user scope"})
        except Exception as exc:
            yield sse("error", {"message": str(exc)})

    return StreamingResponse(stream(), media_type="text/event-stream")
