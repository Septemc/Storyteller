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

    if gen is not None:
        story_text = "".join(list(gen))

    def _is_valid_content(text: str) -> bool:
        if not text:
            return False
        cleaned = text.strip()
        if not cleaned:
            return False
        tags = ['<正文部分>', '<思考过程>', '<内容总结>', '<行动选项>']
        has_any_tag = any(tag in cleaned for tag in tags)
        if has_any_tag:
            body_match = re.search(r'<正文部分>(.*?)</正文部分>', cleaned, re.DOTALL)
            if body_match and body_match.group(1).strip():
                return True
            thinking_match = re.search(r'<思考过程>(.*?)</思考过程>', cleaned, re.DOTALL)
            if thinking_match and thinking_match.group(1).strip():
                return True
            return False
        return len(cleaned) >= 10

    if not _is_valid_content(story_text):
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail="AI返回内容为空，请重试")

    body_match = re.search(r'<正文部分>(.*?)</正文部分>', story_text, re.DOTALL)
    paragraph_word_count = len(body_match.group(1)) if body_match else 0

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
    - event: empty data: {"message": "..."}  # AI返回空内容
    """

    def _sse(event: str, data_obj: Dict) -> str:
        import json

        return f"event: {event}\ndata: {json.dumps(data_obj, ensure_ascii=False)}\n\n"

    def _is_valid_content(text: str) -> bool:
        """检查内容是否有效（非空且包含实际内容）"""
        if not text:
            return False
        cleaned = text.strip()
        if not cleaned:
            return False
        import re
        tags = ['<正文部分>', '<思考过程>', '<内容总结>', '<行动选项>']
        has_any_tag = any(tag in cleaned for tag in tags)
        if has_any_tag:
            body_match = re.search(r'<正文部分>(.*?)</正文部分>', cleaned, re.DOTALL)
            if body_match and body_match.group(1).strip():
                return True
            thinking_match = re.search(r'<思考过程>(.*?)</思考过程>', cleaned, re.DOTALL)
            if thinking_match and thinking_match.group(1).strip():
                return True
            return False
        return len(cleaned) >= 10

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
            if "duration_ms" not in meta_dict:
                meta_dict["duration_ms"] = 0
            
            if dev_log_info:
                yield _sse("dev_log", dev_log_info)
            
            yield _sse("meta", meta_dict)

            if stream_gen is None:
                print(f"[ROUTE_DEBUG] stream_gen is None, full_text len={len(full_text)}")
                story_buf.append(full_text)
                if full_text:
                    yield _sse("delta", {"text": full_text})
            else:
                print(f"[ROUTE_DEBUG] stream_gen is not None, iterating...")
                delta_count = 0
                for delta in stream_gen:
                    delta_count += 1
                    story_buf.append(delta)
                    yield _sse("delta", {"text": delta})
                print(f"[ROUTE_DEBUG] stream_gen iteration done, total deltas: {delta_count}")

            final_text = "".join(story_buf)
            print(f"[ROUTE_DEBUG] final_text length: {len(final_text)}")
            
            if not _is_valid_content(final_text):
                yield _sse("empty", {"message": "AI返回内容为空，请重试"})
                return
            
            body_match = re.search(r'<正文部分>(.*?)</正文部分>', final_text, re.DOTALL)
            paragraph_word_count = len(body_match.group(1)) if body_match else 0

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


class UpdateSegmentRequest(BaseModel):
    segment_id: str
    text: str


def extract_content_parts(text: str) -> Dict[str, Optional[str]]:
    """从文本中提取思考、正文、总结、行动选项四个部分"""
    result = {
        "thinking": None,
        "story": None,
        "summary": None,
        "actions": None
    }
    
    thinking_match = re.search(r'<思考过程>([\s\S]*?)</思考过程>', text)
    if thinking_match:
        result["thinking"] = thinking_match.group(1).strip()
    
    story_match = re.search(r'<正文部分>([\s\S]*?)</正文部分>', text)
    if story_match:
        result["story"] = story_match.group(1).strip()
    
    summary_match = re.search(r'<内容总结>([\s\S]*?)</内容总结>', text)
    if summary_match:
        result["summary"] = summary_match.group(1).strip()
    
    actions_match = re.search(r'<行动选项>([\s\S]*?)</行动选项>', text)
    if actions_match:
        result["actions"] = actions_match.group(1).strip()
    
    return result


@router.post("/story/update_segment")
def update_segment(
    req: UpdateSegmentRequest,
    db: Session = Depends(get_db),
):
    """更新故事片段内容并重新提取各部分"""
    segment = (
        db.query(models.StorySegment)
        .filter(models.StorySegment.segment_id == req.segment_id)
        .first()
    )
    
    if not segment:
        return {"success": False, "message": "Segment not found"}
    
    segment.text = req.text
    
    parts = extract_content_parts(req.text)
    segment.content_thinking = parts["thinking"]
    segment.content_story = parts["story"]
    segment.content_summary = parts["summary"]
    segment.content_actions = parts["actions"]
    
    if parts["story"]:
        segment.paragraph_word_count = len(parts["story"])
    
    db.commit()
    
    return {
        "success": True,
        "segment_id": req.segment_id,
        "extracted": {
            "has_thinking": parts["thinking"] is not None,
            "has_story": parts["story"] is not None,
            "has_summary": parts["summary"] is not None,
            "has_actions": parts["actions"] is not None,
            "word_count": segment.paragraph_word_count
        }
    }


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
            "order_index": seg.order_index,
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


class DeleteSegmentCascadeRequest(BaseModel):
    session_id: str
    from_order_index: int


@router.post("/story/segments/delete_cascade")
def delete_segment_cascade(req: DeleteSegmentCascadeRequest, db: Session = Depends(get_db)):
    """删除指定段及其后续所有段（链式删除）"""
    session = db.query(models.SessionState).filter(
        models.SessionState.session_id == req.session_id
    ).first()
    
    if not session:
        return {"success": False, "message": "存档不存在"}
    
    deleted_count = db.query(models.StorySegment).filter(
        models.StorySegment.session_id == req.session_id,
        models.StorySegment.order_index >= req.from_order_index
    ).delete()
    
    remaining_segments = db.query(models.StorySegment).filter(
        models.StorySegment.session_id == req.session_id
    ).order_by(models.StorySegment.order_index).all()
    
    total_words = sum(seg.paragraph_word_count or 0 for seg in remaining_segments)
    session.total_word_count = total_words
    db.commit()
    
    return {
        "success": True,
        "deleted_count": deleted_count,
        "remaining_count": len(remaining_segments)
    }


class CopySaveFromSegmentRequest(BaseModel):
    source_session_id: str
    to_order_index: int


@router.post("/story/saves/copy_from_segment")
def copy_save_from_segment(req: CopySaveFromSegmentRequest, db: Session = Depends(get_db)):
    """从指定段创建副本存档（包含从第1段到指定段的所有内容）"""
    import time
    import json
    
    source_session = db.query(models.SessionState).filter(
        models.SessionState.session_id == req.source_session_id
    ).first()
    
    if not source_session:
        return {"success": False, "message": "源存档不存在"}
    
    source_segments = db.query(models.StorySegment).filter(
        models.StorySegment.session_id == req.source_session_id,
        models.StorySegment.order_index <= req.to_order_index
    ).order_by(models.StorySegment.order_index).all()
    
    if not source_segments:
        return {"success": False, "message": "没有可复制的段"}
    
    timestamp = int(time.time() * 1000)
    time_suffix = time.strftime("%H%M%S")
    new_session_id = f"S_{timestamp}_{time_suffix}"
    
    new_session = models.SessionState(
        session_id=new_session_id,
        total_word_count=sum(seg.paragraph_word_count or 0 for seg in source_segments),
    )
    
    try:
        source_state = json.loads(source_session.global_state_json) if source_session.global_state_json else {}
        source_state["display_name"] = f"副本_{source_state.get('display_name', req.source_session_id[:12])}"
        new_session.global_state_json = json.dumps(source_state, ensure_ascii=False)
    except:
        new_session.global_state_json = json.dumps({"display_name": f"副本_{req.source_session_id[:12]}"}, ensure_ascii=False)
    
    db.add(new_session)
    
    for seg in source_segments:
        new_segment = models.StorySegment(
            segment_id=f"{new_session_id}_{seg.order_index}",
            session_id=new_session_id,
            order_index=seg.order_index,
            user_input=seg.user_input,
            text=seg.text,
            dungeon_id=seg.dungeon_id,
            dungeon_node_id=seg.dungeon_node_id,
            paragraph_word_count=seg.paragraph_word_count,
            cumulative_word_count=seg.cumulative_word_count,
            frontend_duration=seg.frontend_duration,
            backend_duration=seg.backend_duration,
            content_thinking=seg.content_thinking,
            content_story=seg.content_story,
            content_summary=seg.content_summary,
            content_actions=seg.content_actions,
        )
        db.add(new_segment)
    
    db.commit()
    
    return {
        "success": True,
        "new_session_id": new_session_id,
        "copied_segments": len(source_segments)
    }
