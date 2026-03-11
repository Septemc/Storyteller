import json

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.core import orchestrator, prompts
from backend.db import models
from backend.db.base import Base


@pytest.fixture()
def db_session():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _create_user(db, user_id: str, username: str):
    user = models.User(
        user_id=user_id,
        username=username,
        password_hash="hashed",
        role=models.UserRole.USER,
        is_active=True,
    )
    db.add(user)
    db.commit()
    return user


def _ensure_active_preset_and_llm(db, user_id: str):
    preset_data = prompts.create_minimal_preset(name=f"preset_{user_id}")
    preset = models.DBPreset(
        id=f"preset_{user_id}",
        user_id=user_id,
        name=f"preset_{user_id}",
        version=1,
        is_active=True,
        is_default=True,
        config_json=json.dumps(preset_data, ensure_ascii=False),
    )
    llm = models.DBLLMConfig(
        id=f"llm_{user_id}",
        user_id=user_id,
        name=f"llm_{user_id}",
        base_url="http://mock-llm.local",
        api_key="mock-key",
        stream=False,
        default_model="mock-model",
        is_active=True,
    )
    db.add_all([preset, llm])
    db.commit()


def test_generate_story_context_isolated_by_user(db_session, monkeypatch):
    _create_user(db_session, "u1", "u1")
    _create_user(db_session, "u2", "u2")
    _ensure_active_preset_and_llm(db_session, "u1")
    _ensure_active_preset_and_llm(db_session, "u2")

    db_session.add_all(
        [
            models.Character(character_id="u1_main", user_id="u1", type="player", basic_json=json.dumps({"name": "主角一"})),
            models.Character(character_id="u2_main", user_id="u2", type="player", basic_json=json.dumps({"name": "主角二"})),
            models.WorldbookEntry(entry_id="wb_u1", user_id="u1", title="U1设定", content="U1内容", importance=1.0),
            models.WorldbookEntry(entry_id="wb_u2", user_id="u2", title="U2设定", content="U2内容", importance=1.0),
        ]
    )
    db_session.commit()

    def _fake_chat_completion(**kwargs):
        return "<正文部分>测试剧情</正文部分>", None

    monkeypatch.setattr(orchestrator, "chat_completion", _fake_chat_completion)

    text, meta, stream, dev_log = orchestrator.generate_story_text(
        db=db_session,
        session_id="S_ISO",
        user_input="继续剧情",
        force_stream=False,
        user_id="u1",
    )

    assert stream is None
    assert "测试剧情" in text
    assert meta is not None

    context_info = dev_log.get("contextInfo") or {}
    main_character = context_info.get("main_character") or {}
    characters = context_info.get("characters") or []
    worldbook = context_info.get("worldbook") or []

    character_ids = {item.get("character_id") for item in characters}
    worldbook_ids = {item.get("entry_id") for item in worldbook}

    assert main_character.get("character_id") == "u1_main"
    assert "u2_main" not in character_ids
    assert "wb_u1" in worldbook_ids
    assert "wb_u2" not in worldbook_ids


def test_persist_story_segment_avoids_global_segment_id_collision(db_session):
    _create_user(db_session, "u1", "u1")
    _create_user(db_session, "u2", "u2")

    db_session.add(
        models.SessionState(session_id="S_SHARED", user_id="u1", total_word_count=0)
    )
    db_session.add(
        models.StorySegment(
            segment_id="S_SHARED_1",
            session_id="S_SHARED",
            user_id="u2",
            order_index=1,
            text="<正文部分>old</正文部分>",
            paragraph_word_count=1,
            cumulative_word_count=1,
        )
    )
    db_session.commit()

    idx = orchestrator.persist_story_segment(
        db=db_session,
        session_id="S_SHARED",
        story_text="<正文部分>B</正文部分>",
        user_input="B",
        paragraph_word_count=1,
        user_id="u1",
    )
    assert idx == 1

    ids = {
        row.segment_id
        for row in db_session.query(models.StorySegment)
        .filter(models.StorySegment.session_id == "S_SHARED")
        .all()
    }
    assert "S_SHARED_1" in ids
    assert any(item.startswith("S_SHARED_1__u1") for item in ids)
