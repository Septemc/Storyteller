import json

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.core.auth import UserCreate, create_user
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


def test_create_user_creates_scoped_default_profiles(db_session):
    db_session.add(
        models.DBPreset(
            id="preset_default",
            user_id=None,
            name="default",
            version=1,
            is_default=True,
            is_active=True,
            config_json=json.dumps({"id": "preset_default", "root": {}, "meta": {}}, ensure_ascii=False),
        )
    )
    db_session.add(
        models.DBRegexProfile(
            id="regex_default",
            user_id=None,
            name="default",
            version=1,
            is_default=True,
            is_active=True,
            config_json=json.dumps({"id": "regex_default", "rules": []}, ensure_ascii=False),
        )
    )
    db_session.commit()

    user = create_user(
        db_session,
        UserCreate(username="u_scope", password="p@ssw0rd"),
    )

    preset_id = f"preset_default__{user.user_id}"
    regex_id = f"regex_default__{user.user_id}"

    preset = (
        db_session.query(models.DBPreset)
        .filter(models.DBPreset.id == preset_id, models.DBPreset.user_id == user.user_id)
        .first()
    )
    regex_profile = (
        db_session.query(models.DBRegexProfile)
        .filter(models.DBRegexProfile.id == regex_id, models.DBRegexProfile.user_id == user.user_id)
        .first()
    )

    assert preset is not None
    assert regex_profile is not None
