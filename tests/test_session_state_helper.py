import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.core.session_state import SessionStateConflictError, ensure_session_state
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


def test_ensure_session_state_reuses_existing_row_in_same_scope(db_session):
    _create_user(db_session, "u1", "u1")
    db_session.add(models.SessionState(session_id="S_EXISTING", user_id="u1", total_word_count=3))
    db_session.commit()

    state = ensure_session_state(db_session, "S_EXISTING", user_id="u1")

    assert state.session_id == "S_EXISTING"
    assert state.user_id == "u1"
    assert db_session.query(models.SessionState).filter(models.SessionState.session_id == "S_EXISTING").count() == 1


def test_ensure_session_state_rejects_cross_scope_reuse(db_session):
    _create_user(db_session, "u1", "u1")
    db_session.add(models.SessionState(session_id="S_CONFLICT", user_id="u1", total_word_count=0))
    db_session.commit()

    with pytest.raises(SessionStateConflictError):
        ensure_session_state(db_session, "S_CONFLICT", user_id=None)
