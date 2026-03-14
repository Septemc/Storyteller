from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.api import routes_story
from backend.db.base import Base
from backend.db import models


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


def test_update_session_context_claims_existing_public_session():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)

    db = TestingSessionLocal()
    try:
        user = _create_user(db, "u_claim", "claim_user")
        db.add(models.SessionState(session_id="S_PUBLIC", user_id=None, total_word_count=0, global_state_json="{}"))
        db.commit()

        req = routes_story.SessionContextUpdateRequest(
            session_id="S_PUBLIC",
            current_script_id=None,
            current_dungeon_id=None,
            current_node_id=None,
            main_character_id=None,
        )
        routes_story.update_session_context(req=req, db=db, current_user=user)

        row = db.query(models.SessionState).filter(models.SessionState.session_id == "S_PUBLIC").first()
        assert row is not None
        assert row.user_id == "u_claim"
    finally:
        db.close()

