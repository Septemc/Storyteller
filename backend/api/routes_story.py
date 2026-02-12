from __future__ import annotations

from typing import Dict, List, Optional

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..db.base import get_db
from ..db import models
from ..core import orchestrator

router = APIRouter()


class StoryGenerateRequest(BaseModel):
    session_id: str
    user_input: str


class StoryMeta(BaseModel):
    scene_title: str = ""
    tags: List[str] = []
    tone: Optional[str] = None
    pacing: Optional[str] = None
    dungeon_progress_hint: Optional[str] = None
    dungeon_name: Optional[str] = None
    dungeon_node_name: Optional[str] = None
    main_character: Optional[Dict] = None
    word_count: Optional[int] = None
    duration_ms: Optional[int] = None


class StoryGenerateResponse(BaseModel):
    story: str
    meta: StoryMeta


class SessionSummaryDungeon(BaseModel):
    name: Optional[str] = None
    current_node_name: Optional[str] = None
    progress_hint: Optional[str] = None


class SessionSummaryCharacter(BaseModel):
    character_id: str
    name: Optional[str] = None
    ability_tier: Optional[str] = None


class SessionSummaryVariables(BaseModel):
    main_character: Optional[Dict] = None
    faction_summary: Optional[str] = None


class SessionSummaryResponse(BaseModel):
    dungeon: Optional[SessionSummaryDungeon] = None
    characters: List[SessionSummaryCharacter] = []
    variables: Optional[SessionSummaryVariables] = None


@router.post("/story/generate", response_model=StoryGenerateResponse)
def generate_story(req: StoryGenerateRequest, db: Session = Depends(get_db)) -> StoryGenerateResponse:
    """非流式生成（兼容原前端）。"""
    story_text, meta_obj, gen = orchestrator.generate_story_text(
        db=db,
        session_id=req.session_id,
        user_input=req.user_input,
        force_stream=False,
    )

    # force_stream=False 时 gen 必为空
    if gen is not None:
        story_text = "".join(list(gen))

    orchestrator.persist_story_segment(db, req.session_id, story_text)

    meta = StoryMeta(**(meta_obj.__dict__ if hasattr(meta_obj, "__dict__") else dict(meta_obj)))
    meta.word_count = len(story_text)

    return StoryGenerateResponse(story=story_text, meta=meta)


@router.post("/story/generate_stream")
def generate_story_stream(req: StoryGenerateRequest, db: Session = Depends(get_db)):
    """流式生成：SSE(text/event-stream)。

    事件：
    - event: meta  data: {json}
    - event: delta data: {"text": "..."}
    - event: done  data: {}
    - event: error data: {"message": "..."}
    """

    def _sse(event: str, data_obj: Dict) -> str:
        import json

        return f"event: {event}\ndata: {json.dumps(data_obj, ensure_ascii=False)}\n\n"

    def _gen():
        story_buf: List[str] = []
        try:
            full_text, meta_obj, stream_gen = orchestrator.generate_story_text(
                db=db,
                session_id=req.session_id,
                user_input=req.user_input,
                force_stream=True,
            )

            meta_dict = meta_obj.__dict__ if hasattr(meta_obj, "__dict__") else dict(meta_obj)
            yield _sse("meta", meta_dict)

            if stream_gen is None:
                # 后端可能没有可流式的模型配置；直接一次性返回
                story_buf.append(full_text)
                if full_text:
                    yield _sse("delta", {"text": full_text})
            else:
                for delta in stream_gen:
                    story_buf.append(delta)
                    yield _sse("delta", {"text": delta})

            final_text = "".join(story_buf)
            orchestrator.persist_story_segment(db, req.session_id, final_text)

            yield _sse("done", {})
        except Exception as e:
            yield _sse("error", {"message": str(e)})

    return StreamingResponse(_gen(), media_type="text/event-stream")


@router.get("/session/summary", response_model=SessionSummaryResponse)
def get_session_summary(
    session_id: str = Query(..., description="会话 ID"),
    db: Session = Depends(get_db),
) -> SessionSummaryResponse:
    """会话摘要：供主剧情侧边栏刷新使用（最小可用）。"""

    session_state = db.query(models.SessionState).filter(models.SessionState.session_id == session_id).first()

    dungeon_block: Optional[SessionSummaryDungeon] = None
    if session_state and session_state.current_dungeon_id:
        dungeon = db.query(models.Dungeon).filter(models.Dungeon.dungeon_id == session_state.current_dungeon_id).first()
        node_name = None
        if session_state.current_node_id:
            node = (
                db.query(models.DungeonNode)
                .filter(
                    models.DungeonNode.dungeon_id == session_state.current_dungeon_id,
                    models.DungeonNode.node_id == session_state.current_node_id,
                )
                .first()
            )
            if node:
                node_name = node.name

        dungeon_block = SessionSummaryDungeon(
            name=dungeon.name if dungeon else None,
            current_node_name=node_name,
            progress_hint="最小骨架：未实现真实进度计算",
        )

    # 角色概览
    characters_rows = db.query(models.Character).limit(5).all()
    characters: List[SessionSummaryCharacter] = []

    import json

    for ch in characters_rows:
        name = None
        ability_tier = None
        if ch.basic_json:
            try:
                basic = json.loads(ch.basic_json)
                name = basic.get("name") or basic.get("姓名")
                ability_tier = basic.get("ability_tier") or basic.get("能力评级")
            except Exception:
                pass

        characters.append(
            SessionSummaryCharacter(
                character_id=ch.character_id,
                name=name,
                ability_tier=ability_tier,
            )
        )

    variables = SessionSummaryVariables(
        main_character=None,
        faction_summary=None,
    )

    return SessionSummaryResponse(
        dungeon=dungeon_block,
        characters=characters,
        variables=variables,
    )
