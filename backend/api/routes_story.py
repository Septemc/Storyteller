from __future__ import annotations

import re
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
    frontend_duration: Optional[float] = None


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
    segment_id: Optional[str] = None
    dev_log_info: Optional[Dict] = None


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
    story_text, meta_obj, gen, dev_log_info = orchestrator.generate_story_text(
        db=db,
        session_id=req.session_id,
        user_input=req.user_input,
        force_stream=False,
    )

    # force_stream=False 时 gen 必为空
    if gen is not None:
        story_text = "".join(list(gen))

    # 计算正文字数
    import re
    body_match = re.search(r'<正文部分>(.*?)</正文部分>', story_text, re.DOTALL)
    paragraph_word_count = len(body_match.group(1)) if body_match else 0

    # 获取后端耗时
    backend_duration = meta_obj.duration_ms if hasattr(meta_obj, 'duration_ms') else 0

    order_index = orchestrator.persist_story_segment(
        db,
        req.session_id,
        story_text,
        req.user_input,
        paragraph_word_count=paragraph_word_count,
        frontend_duration=req.frontend_duration or 0.0,
        backend_duration=float(backend_duration),
    )

    segment_id = f"{req.session_id}_{order_index}"

    meta = StoryMeta(**(meta_obj.__dict__ if hasattr(meta_obj, "__dict__") else dict(meta_obj)))
    meta.word_count = paragraph_word_count

    return StoryGenerateResponse(story=story_text, meta=meta, segment_id=segment_id, dev_log_info=dev_log_info)


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
        import re
        story_buf: List[str] = []
        try:
            full_text, meta_obj, stream_gen, dev_log_info = orchestrator.generate_story_text(
                db=db,
                session_id=req.session_id,
                user_input=req.user_input,
                force_stream=True,
            )

            meta_dict = meta_obj.__dict__ if hasattr(meta_obj, "__dict__") else dict(meta_obj)
            # 确保meta_dict中包含duration_ms字段
            if "duration_ms" not in meta_dict:
                meta_dict["duration_ms"] = 0
            
            # 发送开发者日志信息
            if dev_log_info:
                yield _sse("dev_log", dev_log_info)
            
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
            
            # 计算正文字数
            body_match = re.search(r'<正文部分>(.*?)</正文部分>', final_text, re.DOTALL)
            paragraph_word_count = len(body_match.group(1)) if body_match else 0

            # 获取后端耗时
            backend_duration = meta_obj.duration_ms if hasattr(meta_obj, 'duration_ms') else 0

            orchestrator.persist_story_segment(
                db,
                req.session_id,
                final_text,
                req.user_input,
                paragraph_word_count=paragraph_word_count,
                frontend_duration=req.frontend_duration or 0.0,
                backend_duration=float(backend_duration),
            )

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


class StorySegmentItem(BaseModel):
    segment_id: str
    order_index: int
    user_input: Optional[str] = None
    text: str
    paragraph_word_count: int = 0
    cumulative_word_count: int = 0
    frontend_duration: float = 0.0
    backend_duration: float = 0.0
    created_at: Optional[str] = None


class RecentSegmentsResponse(BaseModel):
    segments: List[StorySegmentItem]


@router.get("/story/recent", response_model=RecentSegmentsResponse)
def get_recent_segments(
    session_id: str = Query(..., description="会话 ID"),
    limit: int = Query(5, description="返回的记录数量"),
    db: Session = Depends(get_db),
) -> RecentSegmentsResponse:
    """获取最近的故事片段记录（包含用户输入和AI回复）。"""
    
    segments = (
        db.query(models.StorySegment)
        .filter(models.StorySegment.session_id == session_id)
        .order_by(models.StorySegment.order_index.desc())
        .limit(limit)
        .all()
    )
    
    segments.reverse()
    
    result = []
    for seg in segments:
        result.append(
            StorySegmentItem(
                segment_id=seg.segment_id,
                order_index=seg.order_index,
                user_input=seg.user_input,
                text=seg.text,
                paragraph_word_count=seg.paragraph_word_count or 0,
                cumulative_word_count=seg.cumulative_word_count or 0,
                frontend_duration=seg.frontend_duration or 0.0,
                backend_duration=seg.backend_duration or 0.0,
                created_at=seg.created_at.isoformat() if seg.created_at else None,
            )
        )
    
    return RecentSegmentsResponse(segments=result)


class UpdateFrontendDurationRequest(BaseModel):
    segment_id: str
    frontend_duration: float


@router.post("/story/update_frontend_duration")
def update_frontend_duration(
    req: UpdateFrontendDurationRequest,
    db: Session = Depends(get_db),
):
    """更新故事片段的前端耗时"""
    segment = (
        db.query(models.StorySegment)
        .filter(models.StorySegment.segment_id == req.segment_id)
        .first()
    )
    
    if not segment:
        return {"success": False, "message": "Segment not found"}
    
    segment.frontend_duration = req.frontend_duration
    db.commit()
    
    return {"success": True}


class SaveInfo(BaseModel):
    session_id: str
    display_name: str
    segment_count: int
    total_word_count: int
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class SaveDetail(BaseModel):
    session_id: str
    display_name: str
    segment_count: int
    total_word_count: int
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    segments: List[dict] = []


class SaveRenameRequest(BaseModel):
    session_id: str
    display_name: str


@router.get("/story/saves/list", response_model=List[SaveInfo])
def list_saves(db: Session = Depends(get_db)):
    """获取所有存档列表"""
    sessions = db.query(models.SessionState).order_by(
        models.SessionState.updated_at.desc()
    ).all()
    
    saves = []
    for session in sessions:
        segment_count = db.query(models.StorySegment).filter(
            models.StorySegment.session_id == session.session_id
        ).count()
        
        display_name = session.session_id
        if session.global_state_json:
            try:
                import json
                state = json.loads(session.global_state_json)
                if state.get("display_name"):
                    display_name = state["display_name"]
            except:
                pass
        
        saves.append(SaveInfo(
            session_id=session.session_id,
            display_name=display_name,
            segment_count=segment_count,
            total_word_count=session.total_word_count or 0,
            created_at=session.updated_at.isoformat() if session.updated_at else None,
            updated_at=session.updated_at.isoformat() if session.updated_at else None,
        ))
    
    return saves


@router.get("/story/saves/detail", response_model=SaveDetail)
def get_save_detail(session_id: str = Query(..., description="会话 ID"), db: Session = Depends(get_db)):
    """获取存档详情"""
    session = db.query(models.SessionState).filter(
        models.SessionState.session_id == session_id
    ).first()
    
    if not session:
        return SaveDetail(
            session_id=session_id,
            display_name="未知存档",
            segment_count=0,
            total_word_count=0,
            segments=[]
        )
    
    segments = db.query(models.StorySegment).filter(
        models.StorySegment.session_id == session_id
    ).order_by(models.StorySegment.order_index).all()
    
    segment_list = []
    for seg in segments:
        preview = ""
        content_summary = getattr(seg, 'content_summary', None)
        user_input = getattr(seg, 'user_input', None)
        text = getattr(seg, 'text', None)
        
        if content_summary:
            preview = content_summary[:80] + "..." if len(content_summary) > 80 else content_summary
        elif user_input:
            preview = user_input[:80] + "..." if len(user_input) > 80 else user_input
        elif text:
            first_sentence = re.split(r'[。！？\n]', text)
            if first_sentence and first_sentence[0].strip():
                preview = first_sentence[0].strip()[:80]
                if len(first_sentence[0].strip()) > 80:
                    preview += "..."
            else:
                preview = text[:80] + "..." if len(text) > 80 else text
        
        paragraph_word_count = getattr(seg, 'paragraph_word_count', 0) or 0
        
        segment_list.append({
            "index": seg.order_index,
            "segment_id": seg.segment_id,
            "preview": preview,
            "word_count": paragraph_word_count,
            "created_at": seg.created_at.isoformat() if seg.created_at else None,
        })
    
    display_name = session.session_id
    if session.global_state_json:
        try:
            import json
            state = json.loads(session.global_state_json)
            if state.get("display_name"):
                display_name = state["display_name"]
        except:
            pass
    
    return SaveDetail(
        session_id=session.session_id,
        display_name=display_name,
        segment_count=len(segments),
        total_word_count=session.total_word_count or 0,
        created_at=session.updated_at.isoformat() if session.updated_at else None,
        updated_at=session.updated_at.isoformat() if session.updated_at else None,
        segments=segment_list,
    )


@router.post("/story/saves/rename")
def rename_save(req: SaveRenameRequest, db: Session = Depends(get_db)):
    """重命名存档"""
    session = db.query(models.SessionState).filter(
        models.SessionState.session_id == req.session_id
    ).first()
    
    if not session:
        return {"success": False, "message": "存档不存在"}
    
    import json
    try:
        state = json.loads(session.global_state_json) if session.global_state_json else {}
    except:
        state = {}
    
    state["display_name"] = req.display_name
    session.global_state_json = json.dumps(state, ensure_ascii=False)
    db.commit()
    
    return {"success": True}


@router.post("/story/saves/create")
def create_new_save(db: Session = Depends(get_db)):
    """创建新存档"""
    import time
    timestamp = int(time.time() * 1000)
    time_suffix = time.strftime("%H%M%S")
    session_id = f"S_{timestamp}_{time_suffix}"
    
    session = models.SessionState(
        session_id=session_id,
        total_word_count=0,
    )
    db.add(session)
    db.commit()
    
    return {"success": True, "session_id": session_id}


@router.post("/story/saves/delete")
def delete_save(session_id: str = Query(..., description="会话 ID"), db: Session = Depends(get_db)):
    """删除存档"""
    session = db.query(models.SessionState).filter(
        models.SessionState.session_id == session_id
    ).first()
    
    if not session:
        return {"success": False, "message": "存档不存在"}
    
    db.query(models.StorySegment).filter(
        models.StorySegment.session_id == session_id
    ).delete()
    
    db.delete(session)
    db.commit()
    
    return {"success": True}
