from datetime import datetime
from time import perf_counter
from typing import List, Optional, Dict

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..db.base import get_db
from ..db import models

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
def generate_story(
    req: StoryGenerateRequest,
    db: Session = Depends(get_db),
) -> StoryGenerateResponse:
    """
    最小可运行版本：
    - 初始化或更新 SessionState
    - 写入一条 StorySegment
    - 返回占位剧情文本和简单 meta

    你后续可以在这里接入真正的 orchestrator / LLM。
    """
    t0 = perf_counter()

    session_state = (
        db.query(models.SessionState)
        .filter(models.SessionState.session_id == req.session_id)
        .first()
    )
    if session_state is None:
        session_state = models.SessionState(
            session_id=req.session_id,
            current_dungeon_id=None,
            current_node_id=None,
            total_word_count=0,
        )
        db.add(session_state)
        db.commit()
        db.refresh(session_state)

    story_text = (
        f"【占位剧情】你刚刚执行了操作：“{req.user_input}”。\n\n"
        f"这里是最小可运行后端的占位输出。\n"
        f"你可以在 backend/api/routes_story.py 中替换 generate_story 函数，"
        f"调用 orchestrator 与真实模型来生成真正的剧情内容。"
    )

    word_count = len(story_text)
    existing_count = (
        db.query(models.StorySegment)
        .filter(models.StorySegment.session_id == req.session_id)
        .count()
    )
    order_index = existing_count + 1

    seg = models.StorySegment(
        segment_id=f"{req.session_id}_{order_index}",
        session_id=req.session_id,
        order_index=order_index,
        text=story_text,
        created_at=datetime.utcnow(),
    )
    db.add(seg)

    session_state.total_word_count = (session_state.total_word_count or 0) + word_count
    db.commit()

    t1 = perf_counter()
    duration_ms = int((t1 - t0) * 1000)

    meta = StoryMeta(
        scene_title=f"占位场景 #{order_index}",
        tags=["stub", "demo"],
        tone="中性",
        pacing="平缓推进",
        dungeon_progress_hint="尚未接入副本进度逻辑",
        word_count=word_count,
        duration_ms=duration_ms,
    )

    return StoryGenerateResponse(story=story_text, meta=meta)


@router.get("/session/summary", response_model=SessionSummaryResponse)
def get_session_summary(
    session_id: str = Query(..., description="会话 ID"),
    db: Session = Depends(get_db),
) -> SessionSummaryResponse:
    """
    会话摘要的最小骨架实现：
    - 返回当前副本名（如果有）
    - 返回几条角色概要（如果有）
    - 变量信息目前为空，占位等待你后续接入变量思考模块。
    """
    session_state = (
        db.query(models.SessionState)
        .filter(models.SessionState.session_id == session_id)
        .first()
    )

    dungeon_block: Optional[SessionSummaryDungeon] = None
    if session_state and session_state.current_dungeon_id:
        dungeon = (
            db.query(models.Dungeon)
            .filter(models.Dungeon.dungeon_id == session_state.current_dungeon_id)
            .first()
        )
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

    characters_rows = db.query(models.Character).limit(5).all()
    characters: List[SessionSummaryCharacter] = []

    import json

    for ch in characters_rows:
        name = None
        ability_tier = None
        if ch.basic_json:
            try:
                basic = json.loads(ch.basic_json)
                name = basic.get("name")
                ability_tier = basic.get("ability_tier")
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
