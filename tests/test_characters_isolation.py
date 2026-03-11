import json

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.api import routes_characters
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


def test_list_characters_owner_plus_public(db_session):
    u1 = _create_user(db_session, "u1", "u1")
    _create_user(db_session, "u2", "u2")

    db_session.add_all(
        [
            models.Character(
                character_id="public_char",
                user_id=None,
                type="npc",
                basic_json=json.dumps({"name": "public"}, ensure_ascii=False),
            ),
            models.Character(
                character_id="u1_char",
                user_id="u1",
                type="npc",
                basic_json=json.dumps({"name": "u1"}, ensure_ascii=False),
            ),
            models.Character(
                character_id="u2_char",
                user_id="u2",
                type="npc",
                basic_json=json.dumps({"name": "u2"}, ensure_ascii=False),
            ),
        ]
    )
    db_session.commit()

    resp = routes_characters.list_characters(q=None, db=db_session, current_user=u1)
    ids = {item.character_id for item in resp.items}
    assert "public_char" in ids
    assert "u1_char" in ids
    assert "u2_char" not in ids


def test_import_characters_resolves_cross_user_id_conflict(db_session):
    _create_user(db_session, "u1", "u1")
    u2 = _create_user(db_session, "u2", "u2")

    db_session.add(models.Character(character_id="NPC_1", user_id="u1", type="npc"))
    db_session.commit()

    routes_characters.import_characters(
        payload=[{"character_id": "NPC_1", "type": "npc", "tab_basic": {"name": "new"}}],
        db=db_session,
        current_user=u2,
    )

    rows = (
        db_session.query(models.Character)
        .filter(models.Character.user_id == "u2")
        .all()
    )
    ids = {row.character_id for row in rows}
    assert any(item.startswith("NPC_1__u2") for item in ids)
