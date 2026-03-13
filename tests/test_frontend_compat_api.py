import json
import re

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.core.auth import create_access_token, get_password_hash, verify_password
from backend.db import models
from backend.db.base import Base, get_db
from backend.main import app


@pytest.fixture()
def db_session():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
    Base.metadata.create_all(engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture()
def client(db_session):
    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def _create_user(db_session, user_id: str, username: str, password: str = "p@ssw0rd"):
    user = models.User(
        user_id=user_id,
        username=username,
        password_hash=get_password_hash(password),
        nickname=username,
        role=models.UserRole.USER,
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


def _auth_headers(user_id: str):
    token = create_access_token({"sub": user_id})
    return {"Authorization": f"Bearer {token}"}


def test_auth_profile_and_password_compat_aliases(client, db_session):
    user = _create_user(db_session, "u_front", "front_user", password="old-pass")
    headers = _auth_headers(user.user_id)

    profile_resp = client.put(
        "/api/auth/profile",
        headers=headers,
        json={"nickname": "Front User", "email": "front@example.com"},
    )
    assert profile_resp.status_code == 200
    assert profile_resp.json()["nickname"] == "Front User"
    assert profile_resp.json()["email"] == "front@example.com"

    password_resp = client.put(
        "/api/auth/password",
        headers=headers,
        json={"current_password": "old-pass", "new_password": "new-pass-123"},
    )
    assert password_resp.status_code == 200
    assert password_resp.json()["success"] is True

    db_session.refresh(user)
    assert user.email == "front@example.com"
    assert user.nickname == "Front User"
    assert verify_password("new-pass-123", user.password_hash)


def test_story_stats_endpoint_matches_frontend_fields(client, db_session):
    user = _create_user(db_session, "u_stats", "stats_user")
    headers = _auth_headers(user.user_id)

    db_session.add(models.Character(character_id="c1", user_id=user.user_id, type="npc"))
    db_session.add(models.WorldbookEntry(entry_id="w1", user_id=user.user_id, title="Alpha", content="Lore", importance=0.6))
    db_session.add(
        models.StorySegment(
            segment_id="seg_1",
            session_id="S1",
            user_id=user.user_id,
            order_index=1,
            text="<正文部分>abc</正文部分>",
            paragraph_word_count=3,
            cumulative_word_count=3,
        )
    )
    db_session.add(
        models.StorySegment(
            segment_id="seg_2",
            session_id="S1",
            user_id=user.user_id,
            order_index=2,
            text="<正文部分>hello</正文部分>",
            paragraph_word_count=5,
            cumulative_word_count=8,
        )
    )
    db_session.commit()

    resp = client.get("/api/story/stats", headers=headers)
    assert resp.status_code == 200
    assert resp.json() == {
        "stories": 2,
        "characters": 1,
        "worldbook": 1,
        "words": 8,
    }


def test_worldbook_semantic_search_is_frontend_compatible_and_user_scoped(client, db_session):
    user_1 = _create_user(db_session, "u_sem_1", "sem_user_1")
    user_2 = _create_user(db_session, "u_sem_2", "sem_user_2")

    db_session.add_all(
        [
            models.WorldbookEntry(
                worldbook_id="Wabc1234",
                entry_id="wb_u1",
                user_id=user_1.user_id,
                category="creatures",
                title="Dragon Archive",
                content="Ancient dragon sleeps beneath the mountain.",
                importance=0.9,
                meta_json=json.dumps({"enabled": True}, ensure_ascii=False),
            ),
            models.WorldbookEntry(
                worldbook_id="Wdef5678",
                entry_id="wb_u2",
                user_id=user_2.user_id,
                category="creatures",
                title="Dragon Secret",
                content="Private enemy dragon data.",
                importance=1.0,
                meta_json=json.dumps({"enabled": True}, ensure_ascii=False),
            ),
        ]
    )
    db_session.commit()

    resp = client.post(
        "/api/worldbook/semantic_search",
        headers=_auth_headers(user_1.user_id),
        json={"query": "dragon mountain", "top_k": 10, "use_hybrid": True},
    )
    assert resp.status_code == 200

    data = resp.json()
    assert "results" in data
    assert any(item["entry_id"] == "wb_u1" for item in data["results"])
    assert all(item["entry_id"] != "wb_u2" for item in data["results"])
    assert all(item["worldbook_id"].startswith("W") for item in data["results"])


def test_worldbook_import_assigns_single_w_prefixed_worldbook_id(client, db_session):
    user = _create_user(db_session, "u_worldbook_import", "wb_import_user")

    resp = client.post(
        "/api/worldbook/import?sync_embeddings=false",
        headers=_auth_headers(user.user_id),
        json={
            "entries": [
                {"title": "设定一", "content": "内容一", "category": "lore"},
                {"title": "设定二", "content": "内容二", "category": "lore"},
            ]
        },
    )

    assert resp.status_code == 200
    data = resp.json()
    assert re.fullmatch(r"W[a-z0-9]{7}", data["worldbook_id"])
    assert data["created"] == 2

    rows = db_session.query(models.WorldbookEntry).filter(models.WorldbookEntry.user_id == user.user_id).all()
    assert len(rows) == 2
    assert {row.worldbook_id for row in rows} == {data["worldbook_id"]}


def test_worldbook_import_accepts_legacy_category_container(client, db_session):
    user = _create_user(db_session, "u_worldbook_legacy", "wb_legacy_user")

    resp = client.post(
        "/api/worldbook/import?sync_embeddings=false",
        headers=_auth_headers(user.user_id),
        json={
            "name": "旧格式设定",
            "categories": {
                "地理": [{"title": "王城", "content": "中心城市"}],
                "人物": [{"title": "国王", "content": "统治者"}],
            },
        },
    )

    assert resp.status_code == 200
    data = resp.json()
    assert re.fullmatch(r"W[a-z0-9]{7}", data["worldbook_id"])

    rows = db_session.query(models.WorldbookEntry).filter(models.WorldbookEntry.user_id == user.user_id).all()
    assert len(rows) == 2
    assert sorted(row.category for row in rows) == ["人物", "地理"]

def test_worldbook_import_updates_public_entry_without_forking_scope(client, db_session):
    user = _create_user(db_session, "u_worldbook_public_edit", "wb_public_editor")
    public_entry = models.WorldbookEntry(
        worldbook_id="Wpub0001",
        entry_id="wb_public_1",
        user_id=None,
        category="lore",
        title="Public Lore",
        content="Before",
        importance=0.5,
        meta_json=json.dumps({"enabled": True, "disable": False}, ensure_ascii=False),
    )
    db_session.add(public_entry)
    db_session.commit()

    resp = client.post(
        "/api/worldbook/import?sync_embeddings=false",
        headers=_auth_headers(user.user_id),
        json={
            "worldbook_id": "Wpub0001",
            "entries": [
                {
                    "entry_id": "wb_public_1",
                    "category": "lore",
                    "title": "Public Lore",
                    "content": "After",
                    "meta": {"enabled": False, "disable": True},
                }
            ],
        },
    )

    assert resp.status_code == 200

    rows = db_session.query(models.WorldbookEntry).filter(models.WorldbookEntry.worldbook_id == "Wpub0001").all()
    assert len(rows) == 1
    assert rows[0].entry_id == "wb_public_1"
    assert rows[0].user_id is None
    assert rows[0].content == "After"
    assert json.loads(rows[0].meta_json) == {"enabled": False, "disable": True}


def test_worldbook_delete_all_can_remove_public_worldbook_for_logged_in_user(client, db_session):
    user = _create_user(db_session, "u_worldbook_public_delete", "wb_public_deleter")
    db_session.add_all(
        [
            models.WorldbookEntry(
                worldbook_id="Wpubdel1",
                entry_id="wb_public_delete_1",
                user_id=None,
                category="lore",
                title="Entry 1",
                content="One",
                importance=0.5,
                meta_json=json.dumps({"enabled": True}, ensure_ascii=False),
            ),
            models.WorldbookEntry(
                worldbook_id="Wpubdel1",
                entry_id="wb_public_delete_2",
                user_id=None,
                category="lore",
                title="Entry 2",
                content="Two",
                importance=0.5,
                meta_json=json.dumps({"enabled": True}, ensure_ascii=False),
            ),
        ]
    )
    db_session.commit()

    resp = client.delete(
        "/api/worldbook/all?confirm=true&worldbook_id=Wpubdel1",
        headers=_auth_headers(user.user_id),
    )

    assert resp.status_code == 200
    assert resp.json()["deleted"] == 2
    assert (
        db_session.query(models.WorldbookEntry)
        .filter(models.WorldbookEntry.worldbook_id == "Wpubdel1")
        .count()
        == 0
    )
