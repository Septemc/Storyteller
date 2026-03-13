import json

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.core.auth import create_access_token, get_password_hash
from backend.db import models
from backend.db.base import Base, get_db
from backend.db.crud.worldbook import cleanup_orphan_worldbook_embeddings
from backend.main import app


@pytest.fixture()
def db_session():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    testing_session_local = sessionmaker(bind=engine, autocommit=False, autoflush=False)
    Base.metadata.create_all(engine)
    db = testing_session_local()
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


def _create_user(db_session, user_id: str, username: str):
    user = models.User(
        user_id=user_id,
        username=username,
        password_hash=get_password_hash("p@ssw0rd"),
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


def test_cleanup_orphan_worldbook_embeddings_removes_mismatched_rows(db_session):
    db_session.add(
        models.WorldbookEntry(
            worldbook_id="Wvalid01",
            entry_id="entry_ok",
            user_id=None,
            category="lore",
            title="Title",
            content="Content",
            meta_json=json.dumps({"enabled": True}, ensure_ascii=False),
        )
    )
    db_session.add_all(
        [
            models.WorldbookEmbedding(
                user_id=None,
                worldbook_id="Wvalid01",
                entry_id="entry_ok",
                embedding_json="[0.1, 0.2]",
                content_hash="hash-ok",
                embedding_model="tfidf",
                dimension=2,
            ),
            models.WorldbookEmbedding(
                user_id=None,
                worldbook_id="Wghost01",
                entry_id="entry_missing",
                embedding_json="[0.3, 0.4]",
                content_hash="hash-bad",
                embedding_model="tfidf",
                dimension=2,
            ),
        ]
    )
    db_session.commit()

    deleted = cleanup_orphan_worldbook_embeddings(db_session)

    assert deleted == 1
    rows = db_session.query(models.WorldbookEmbedding).order_by(models.WorldbookEmbedding.id).all()
    assert len(rows) == 1
    assert rows[0].worldbook_id == "Wvalid01"
    assert rows[0].entry_id == "entry_ok"


def test_delete_worldbook_all_removes_embeddings_by_worldbook_id_even_if_orphaned(client, db_session):
    user = _create_user(db_session, "u_cleanup", "cleanup_user")
    db_session.add(
        models.WorldbookEntry(
            worldbook_id="Wclean01",
            entry_id="entry_live",
            user_id=None,
            category="lore",
            title="Lore",
            content="Content",
            meta_json=json.dumps({"enabled": True}, ensure_ascii=False),
        )
    )
    db_session.add_all(
        [
            models.WorldbookEmbedding(
                user_id=None,
                worldbook_id="Wclean01",
                entry_id="entry_live",
                embedding_json="[0.1, 0.2]",
                content_hash="hash-live",
                embedding_model="tfidf",
                dimension=2,
            ),
            models.WorldbookEmbedding(
                user_id=None,
                worldbook_id="Wclean01",
                entry_id="entry_stale",
                embedding_json="[0.3, 0.4]",
                content_hash="hash-stale",
                embedding_model="tfidf",
                dimension=2,
            ),
        ]
    )
    db_session.commit()

    response = client.delete(
        "/api/worldbook/all?confirm=true&worldbook_id=Wclean01",
        headers=_auth_headers(user.user_id),
    )

    assert response.status_code == 200
    assert db_session.query(models.WorldbookEntry).filter(models.WorldbookEntry.worldbook_id == "Wclean01").count() == 0
    assert db_session.query(models.WorldbookEmbedding).filter(models.WorldbookEmbedding.worldbook_id == "Wclean01").count() == 0
