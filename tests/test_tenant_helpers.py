import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.core.tenant import owner_only, owner_or_public, resolve_scoped_id
from backend.db.base import Base
from backend.db import models


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


def test_owner_and_visible_filters(db_session):
    _create_user(db_session, "u1", "u1")
    _create_user(db_session, "u2", "u2")

    db_session.add_all(
        [
            models.Character(character_id="public_char", user_id=None, type="npc"),
            models.Character(character_id="u1_char", user_id="u1", type="npc"),
            models.Character(character_id="u2_char", user_id="u2", type="npc"),
        ]
    )
    db_session.commit()

    owner_rows = owner_only(db_session.query(models.Character), models.Character, "u1").all()
    visible_rows = owner_or_public(db_session.query(models.Character), models.Character, "u1").all()
    anon_rows = owner_only(db_session.query(models.Character), models.Character, None).all()

    owner_ids = {row.character_id for row in owner_rows}
    visible_ids = {row.character_id for row in visible_rows}
    anon_ids = {row.character_id for row in anon_rows}

    assert owner_ids == {"u1_char"}
    assert visible_ids == {"u1_char", "public_char"}
    assert anon_ids == {"public_char"}


def test_resolve_scoped_id_when_conflict(db_session):
    _create_user(db_session, "u1", "u1")
    _create_user(db_session, "u2", "u2")

    db_session.add(models.Character(character_id="NPC_1", user_id="u1", type="npc"))
    db_session.commit()

    resolved = resolve_scoped_id(db_session, models.Character, "character_id", "NPC_1", "u2")
    assert resolved.startswith("NPC_1__u2")
