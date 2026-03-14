from __future__ import annotations

import re
import json
from typing import Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..db.base import get_db
from ..db import models
from ..core import orchestrator
from ..core.auth import get_current_user_sync, User as AuthUser
from ..core.session_state import (
    SessionStateConflictError,
    build_unique_session_id,
    ensure_session_state,
)
from ..core.tenant import current_user_id, owner_only

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


class SessionContextUpdateRequest(BaseModel):
    session_id: str
    main_character_id: Optional[str] = None
    current_script_id: Optional[str] = None
    current_dungeon_id: Optional[str] = None
    current_node_id: Optional[str] = None


class SessionContextUpdateResponse(BaseModel):
    success: bool = True
    session_id: str
    main_character_id: Optional[str] = None
    current_script_id: Optional[str] = None
    current_dungeon_id: Optional[str] = None
    current_node_id: Optional[str] = None


class SessionCharactersResponse(BaseModel):
    main_character: Optional[Dict] = None
    characters: List[SessionSummaryCharacter] = []


def _parse_character_basic(ch: models.Character) -> Dict:
    basic = {}
    if ch.basic_json:
        try:
            basic = json.loads(ch.basic_json)
        except Exception:
            basic = {}

    # 兼容 data_json 中的 tab_basic / basic
    if ch.data_json:
        try:
            data = json.loads(ch.data_json)
            if isinstance(data, dict):
                basic = data.get("tab_basic") or data.get("basic") or basic
        except Exception:
            pass

    if not isinstance(basic, dict):
        basic = {}

    # 兼容扁平结构（f_name 等）
    if ch.data_json:
        try:
            data = json.loads(ch.data_json)
            if isinstance(data, dict):
                flat_basic = {
                    k: v
                    for k, v in data.items()
                    if not k.startswith("tab_") and k not in {"character_id", "type", "template_id"}
                }
                if flat_basic:
                    merged = dict(flat_basic)
                    merged.update(basic)
                    basic = merged
        except Exception:
            pass

    return basic


def _first_non_empty(data: Dict, keys: List[str]) -> Optional[str]:
    for key in keys:
        value = data.get(key)
        if value is None:
            continue
        text = str(value).strip()
        if text:
            return text
    return None


def _to_character_summary(ch: models.Character) -> SessionSummaryCharacter:
    basic = _parse_character_basic(ch)
    return SessionSummaryCharacter(
        character_id=ch.character_id,
        name=_first_non_empty(basic, ["name", "姓名", "角色名", "f_name", "f_nickname", "昵称"]),
        ability_tier=_first_non_empty(basic, ["ability_tier", "能力评级", "境界", "f_ability_tier", "f_level", "f_realm", "f_stage"]),
    )


def _ensure_session_state(db: Session, session_id: str, user_id: Optional[str] = None) -> models.SessionState:
    return ensure_session_state(db, session_id, user_id=user_id)


@router.post("/story/generate", response_model=StoryGenerateResponse)
def generate_story(req: StoryGenerateRequest, db: Session = Depends(get_db), current_user: Optional[AuthUser] = Depends(get_current_user_sync)) -> StoryGenerateResponse:
    """非流式生成（兼容原前端）。"""
    user_id = current_user_id(current_user)
    
    try:
        story_text, meta_obj, gen, dev_log_info = orchestrator.generate_story_text(
            db=db,
            session_id=req.session_id,
            user_input=req.user_input,
            force_stream=False,
            user_id=user_id,
        )
    except SessionStateConflictError as exc:
        raise HTTPException(
            status_code=409,
            detail="当前存档属于另一用户作用域。请重新登录后刷新页面，或切换到当前账号自己的存档。",
        ) from exc

    if gen is not None:
        story_text = "".join(list(gen))

    if not orchestrator.is_valid_story_content(story_text):
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail="AI返回内容为空，请重试")

    parts = orchestrator.extract_story_parts(story_text)
    paragraph_word_count = len(parts.get("story") or "")

    backend_duration = meta_obj.duration_ms if hasattr(meta_obj, 'duration_ms') else 0

    order_index = orchestrator.persist_story_segment(
        db,
        req.session_id,
        story_text,
        req.user_input,
        paragraph_word_count=paragraph_word_count,
        frontend_duration=req.frontend_duration or 0.0,
        backend_duration=float(backend_duration),
        user_id=user_id,
    )

    segment = owner_only(
        db.query(models.StorySegment).filter(
            models.StorySegment.session_id == req.session_id,
            models.StorySegment.order_index == order_index,
        ),
        models.StorySegment,
        user_id,
    ).first()
    segment_id = segment.segment_id if segment else f"{req.session_id}_{order_index}"

    meta = StoryMeta(**(meta_obj.__dict__ if hasattr(meta_obj, "__dict__") else dict(meta_obj)))
    meta.word_count = paragraph_word_count

    return StoryGenerateResponse(story=story_text, meta=meta, segment_id=segment_id, dev_log_info=dev_log_info)


@router.post("/story/generate_stream")
def generate_story_stream(req: StoryGenerateRequest, db: Session = Depends(get_db), current_user: Optional[AuthUser] = Depends(get_current_user_sync)):
    """流式生成：SSE(text/event-stream)。
    
    用户过滤：仅返回当前用户的数据
    """

    user_id = current_user_id(current_user)

    def _sse(event: str, data_obj: Dict) -> str:
        import json

        return f"event: {event}\ndata: {json.dumps(data_obj, ensure_ascii=False)}\n\n"

    def _is_valid_content(text: str) -> bool:
        return orchestrator.is_valid_story_content(text)

    def _gen():
        story_buf: List[str] = []
        try:
            full_text, meta_obj, stream_gen, dev_log_info = orchestrator.generate_story_text(
                db=db,
                session_id=req.session_id,
                user_input=req.user_input,
                force_stream=True,
                user_id=user_id,
            )

            meta_dict = meta_obj.__dict__ if hasattr(meta_obj, "__dict__") else dict(meta_obj)
            if "duration_ms" not in meta_dict:
                meta_dict["duration_ms"] = 0
            
            if dev_log_info:
                yield _sse("dev_log", dev_log_info)
            
            yield _sse("meta", meta_dict)

            if stream_gen is None:
                story_buf.append(full_text)
                if full_text:
                    yield _sse("delta", {"text": full_text})
            else:
                for delta in stream_gen:
                    story_buf.append(delta)
                    yield _sse("delta", {"text": delta})

            final_text = "".join(story_buf)
            
            if not _is_valid_content(final_text):
                yield _sse("empty", {"message": "AI返回内容为空，请重试"})
                return
            
            parts = orchestrator.extract_story_parts(final_text)
            paragraph_word_count = len(parts.get("story") or "")

            backend_duration = meta_obj.duration_ms if hasattr(meta_obj, 'duration_ms') else 0

            orchestrator.persist_story_segment(
                db,
                req.session_id,
                final_text,
                req.user_input,
                paragraph_word_count=paragraph_word_count,
                frontend_duration=req.frontend_duration or 0.0,
                backend_duration=float(backend_duration),
                user_id=user_id,
            )

            yield _sse("done", {})
        except SessionStateConflictError:
            yield _sse("error", {"message": "当前存档属于另一用户作用域。请重新登录后刷新页面，或切换到当前账号自己的存档。"})
        except Exception as e:
            yield _sse("error", {"message": str(e)})

    return StreamingResponse(_gen(), media_type="text/event-stream")


@router.post("/session/context", response_model=SessionSummaryResponse)
def update_session_context(
    req: SessionContextUpdateRequest,
    db: Session = Depends(get_db),
    current_user: Optional[AuthUser] = Depends(get_current_user_sync),
) -> SessionSummaryResponse:
    """更新会话上下文并返回会话摘要。"""
    user_id = current_user_id(current_user)

    try:
        session_state = ensure_session_state(db, req.session_id, user_id=user_id)
    except SessionStateConflictError as exc:
        raise HTTPException(
            status_code=409,
            detail="当前存档属于另一用户作用域。请重新登录后刷新页面，或切换到当前账号自己的存档。",
        ) from exc

    provided_fields = getattr(req, "model_fields_set", set())
    if "current_script_id" in provided_fields:
        session_state.current_script_id = req.current_script_id
    if "current_dungeon_id" in provided_fields:
        session_state.current_dungeon_id = req.current_dungeon_id
    if "current_node_id" in provided_fields:
        session_state.current_node_id = req.current_node_id

    global_state = {}
    if session_state.global_state_json:
        try:
            global_state = json.loads(session_state.global_state_json)
        except Exception:
            global_state = {}
    if not isinstance(global_state, dict):
        global_state = {}

    if "main_character_id" in provided_fields:
        if req.main_character_id:
            global_state["main_character_id"] = req.main_character_id
        else:
            global_state.pop("main_character_id", None)

    session_state.global_state_json = json.dumps(global_state, ensure_ascii=False)
    db.commit()
    db.refresh(session_state)

    dungeon_block: Optional[SessionSummaryDungeon] = None
    if session_state and session_state.current_dungeon_id:
        dungeon_query = owner_only(
            db.query(models.Dungeon).filter(models.Dungeon.dungeon_id == session_state.current_dungeon_id),
            models.Dungeon,
            user_id,
        )
        dungeon = dungeon_query.first()
        node_name = None
        progress_hint = "未知"
        if session_state.current_node_id:
            node_query = db.query(models.DungeonNode).filter(
                models.DungeonNode.dungeon_id == session_state.current_dungeon_id,
                models.DungeonNode.node_id == session_state.current_node_id,
            )
            node = node_query.first()
            if node:
                node_name = node.name
                if node.progress_percent is not None:
                    progress_hint = f"{int(node.progress_percent)}%"

        dungeon_block = SessionSummaryDungeon(
            name=dungeon.name if dungeon else None,
            current_node_name=node_name,
            progress_hint=progress_hint,
        )

    # 角色概览
    char_query = owner_only(db.query(models.Character), models.Character, user_id)
    characters_rows = char_query.limit(5).all()
    characters: List[SessionSummaryCharacter] = [_to_character_summary(ch) for ch in characters_rows]

    variable_main_character: Optional[Dict] = None
    main_character_id = global_state.get("main_character_id")
    if main_character_id:
        main_char_query = owner_only(
            db.query(models.Character).filter(models.Character.character_id == main_character_id),
            models.Character,
            user_id,
        )
        main_char = main_char_query.first()
        if main_char:
            basic = _parse_character_basic(main_char)
            variable_main_character = {
                "character_id": main_char.character_id,
                "name": _first_non_empty(basic, ["name", "姓名", "角色名", "f_name", "f_nickname", "昵称"]),
                "ability_tier": _first_non_empty(basic, ["ability_tier", "能力评级", "境界", "f_ability_tier", "f_level", "f_realm", "f_stage"]),
                "economy_summary": _first_non_empty(basic, ["economy_summary", "经济", "资源", "f_economy", "f_resources", "f_money", "f_wealth"]),
            }

    variables = SessionSummaryVariables(
        main_character=variable_main_character,
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
    current_user: Optional[AuthUser] = Depends(get_current_user_sync),
) -> RecentSegmentsResponse:
    """获取最近的故事片段记录（包含用户输入和AI回复）。"""
    user_id = current_user_id(current_user)

    query = owner_only(
        db.query(models.StorySegment).filter(models.StorySegment.session_id == session_id),
        models.StorySegment,
        user_id,
    )
    
    segments = query.order_by(models.StorySegment.order_index.desc()).limit(limit).all()
    
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
    current_user: Optional[AuthUser] = Depends(get_current_user_sync),
):
    """更新故事片段的前端耗时"""
    user_id = current_user_id(current_user)
    segment = owner_only(
        db.query(models.StorySegment).filter(models.StorySegment.segment_id == req.segment_id),
        models.StorySegment,
        user_id,
    ).first()
    
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
    return orchestrator.extract_story_parts(text)


@router.post("/story/update_segment")
def update_segment(
    req: UpdateSegmentRequest,
    db: Session = Depends(get_db),
    current_user: Optional[AuthUser] = Depends(get_current_user_sync),
):
    """更新故事片段内容并重新提取各部分"""
    user_id = current_user_id(current_user)
    segment = owner_only(
        db.query(models.StorySegment).filter(models.StorySegment.segment_id == req.segment_id),
        models.StorySegment,
        user_id,
    ).first()
    
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


@router.get("/story/stats")
def get_story_stats(
    db: Session = Depends(get_db),
    current_user: Optional[AuthUser] = Depends(get_current_user_sync),
):
    user_id = current_user_id(current_user)

    if not user_id:
        return {
            "stories": 0,
            "characters": 0,
            "worldbook": 0,
            "words": 0,
        }

    story_segments = owner_only(
        db.query(models.StorySegment),
        models.StorySegment,
        user_id,
    ).all()

    return {
        "stories": len(story_segments),
        "characters": owner_only(db.query(models.Character), models.Character, user_id).count(),
        "worldbook": owner_only(db.query(models.WorldbookEntry), models.WorldbookEntry, user_id).count(),
        "words": sum((segment.paragraph_word_count or 0) for segment in story_segments),
    }


@router.get("/story/saves/list", response_model=List[SaveInfo])
def list_saves(db: Session = Depends(get_db), current_user: Optional[AuthUser] = Depends(get_current_user_sync)):
    """获取所有存档列表"""
    user_id = current_user_id(current_user)

    query = owner_only(db.query(models.SessionState), models.SessionState, user_id)
    sessions = query.order_by(models.SessionState.updated_at.desc()).all()
    
    saves = []
    for session in sessions:
        seg_query = owner_only(
            db.query(models.StorySegment).filter(models.StorySegment.session_id == session.session_id),
            models.StorySegment,
            user_id,
        )
        segment_count = seg_query.count()
        
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
def get_save_detail(session_id: str = Query(..., description="会话 ID"), db: Session = Depends(get_db), current_user: Optional[AuthUser] = Depends(get_current_user_sync)):
    """获取存档详情"""
    user_id = current_user_id(current_user)

    session_query = owner_only(
        db.query(models.SessionState).filter(models.SessionState.session_id == session_id),
        models.SessionState,
        user_id,
    )
    session = session_query.first()
    
    if not session:
        return SaveDetail(
            session_id=session_id,
            display_name="未知存档",
            segment_count=0,
            total_word_count=0,
            segments=[]
        )
    
    seg_query = owner_only(
        db.query(models.StorySegment).filter(models.StorySegment.session_id == session_id),
        models.StorySegment,
        user_id,
    )
    segments = seg_query.order_by(models.StorySegment.order_index).all()
    
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
def rename_save(req: SaveRenameRequest, db: Session = Depends(get_db), current_user: Optional[AuthUser] = Depends(get_current_user_sync)):
    """重命名存档"""
    user_id = current_user_id(current_user)

    session_query = owner_only(
        db.query(models.SessionState).filter(models.SessionState.session_id == req.session_id),
        models.SessionState,
        user_id,
    )
    session = session_query.first()
    
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
def create_new_save(db: Session = Depends(get_db), current_user: Optional[AuthUser] = Depends(get_current_user_sync)):
    """创建新存档"""
    user_id = current_user_id(current_user)
    session_id = build_unique_session_id(user_id=user_id)
    
    session = models.SessionState(
        session_id=session_id,
        total_word_count=0,
        user_id=user_id,
    )
    db.add(session)
    db.commit()
    
    return {"success": True, "session_id": session_id}


@router.post("/story/saves/delete")
def delete_save(session_id: str = Query(..., description="会话 ID"), db: Session = Depends(get_db), current_user: Optional[AuthUser] = Depends(get_current_user_sync)):
    """删除存档"""
    user_id = current_user_id(current_user)

    session_query = owner_only(
        db.query(models.SessionState).filter(models.SessionState.session_id == session_id),
        models.SessionState,
        user_id,
    )
    session = session_query.first()
    
    if not session:
        return {"success": False, "message": "存档不存在"}
    
    seg_query = owner_only(
        db.query(models.StorySegment).filter(models.StorySegment.session_id == session_id),
        models.StorySegment,
        user_id,
    )
    seg_query.delete()
    
    db.delete(session)
    db.commit()
    
    return {"success": True}


class DeleteSegmentCascadeRequest(BaseModel):
    session_id: str
    from_order_index: int


@router.post("/story/segments/delete_cascade")
def delete_segment_cascade(req: DeleteSegmentCascadeRequest, db: Session = Depends(get_db), current_user: Optional[AuthUser] = Depends(get_current_user_sync)):
    """删除指定段及其后续所有段（链式删除）"""
    user_id = current_user_id(current_user)

    session_query = owner_only(
        db.query(models.SessionState).filter(models.SessionState.session_id == req.session_id),
        models.SessionState,
        user_id,
    )
    session = session_query.first()
    
    if not session:
        return {"success": False, "message": "存档不存在"}
    
    del_query = owner_only(
        db.query(models.StorySegment).filter(
            models.StorySegment.session_id == req.session_id,
            models.StorySegment.order_index >= req.from_order_index,
        ),
        models.StorySegment,
        user_id,
    )
    deleted_count = del_query.delete()
    
    remain_query = owner_only(
        db.query(models.StorySegment).filter(models.StorySegment.session_id == req.session_id),
        models.StorySegment,
        user_id,
    )
    remaining_segments = remain_query.order_by(models.StorySegment.order_index).all()
    
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
def copy_save_from_segment(req: CopySaveFromSegmentRequest, db: Session = Depends(get_db), current_user: Optional[AuthUser] = Depends(get_current_user_sync)):
    """从指定段创建副本存档（包含从第1段到指定段的所有内容）"""
    import json
    user_id = current_user_id(current_user)

    source_query = owner_only(
        db.query(models.SessionState).filter(models.SessionState.session_id == req.source_session_id),
        models.SessionState,
        user_id,
    )
    source_session = source_query.first()
    
    if not source_session:
        return {"success": False, "message": "源存档不存在"}
    
    seg_query = owner_only(
        db.query(models.StorySegment).filter(
            models.StorySegment.session_id == req.source_session_id,
            models.StorySegment.order_index <= req.to_order_index,
        ),
        models.StorySegment,
        user_id,
    )
    source_segments = seg_query.order_by(models.StorySegment.order_index).all()
    
    if not source_segments:
        return {"success": False, "message": "没有可复制的段"}
    
    new_session_id = build_unique_session_id(user_id=user_id)
    
    new_session = models.SessionState(
        session_id=new_session_id,
        total_word_count=sum(seg.paragraph_word_count or 0 for seg in source_segments),
        user_id=user_id,
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
            user_id=user_id,
        )
        db.add(new_segment)
    
    db.commit()
    
    return {
        "success": True,
        "new_session_id": new_session_id,
        "copied_segments": len(source_segments)
    }
