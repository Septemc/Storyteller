"""
SQLite migration for worldbook isolation.

Goals:
1. Add worldbook.worldbook_id immediately after user_id.
2. Add worldbook_embeddings.user_id and worldbook_embeddings.worldbook_id,
   with worldbook_id immediately after user_id.
3. Backfill legacy rows.

Legacy note:
- Old data does not preserve "which entries came from the same import batch".
- This migration assigns one unique worldbook_id per legacy entry row to avoid
  accidental cross-book mixing.
"""

import sys
import uuid
from pathlib import Path

from sqlalchemy import inspect, text

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from backend.db.base import engine  # noqa: E402


def _table_exists(table_name: str) -> bool:
    return table_name in inspect(engine).get_table_names()


def _columns(table_name: str):
    if not _table_exists(table_name):
        return []
    return [column["name"] for column in inspect(engine).get_columns(table_name)]


def _generate_worldbook_id() -> str:
    return f"W{uuid.uuid4().hex[:7]}"


def _rebuild_worldbook() -> None:
    if not _table_exists("worldbook"):
        print("skip worldbook rebuild: table missing")
        return
    existing_columns = _columns("worldbook")
    if existing_columns[:4] == ["id", "user_id", "worldbook_id", "entry_id"]:
        print("skip worldbook rebuild")
        return

    with engine.begin() as conn:
        rows = conn.execute(text("SELECT * FROM worldbook")).mappings().all()
        assigned_ids = {row["entry_id"]: row.get("worldbook_id") or _generate_worldbook_id() for row in rows}

        conn.execute(text("PRAGMA foreign_keys=OFF"))
        conn.execute(text("ALTER TABLE worldbook RENAME TO worldbook_legacy"))
        conn.execute(
            text(
                """
                CREATE TABLE worldbook (
                    id INTEGER PRIMARY KEY,
                    user_id VARCHAR(32),
                    worldbook_id VARCHAR(8) NOT NULL,
                    entry_id VARCHAR NOT NULL UNIQUE,
                    category VARCHAR,
                    tags VARCHAR,
                    title VARCHAR NOT NULL,
                    content TEXT NOT NULL,
                    importance FLOAT,
                    canonical BOOLEAN,
                    meta_json TEXT,
                    created_at DATETIME,
                    updated_at DATETIME,
                    FOREIGN KEY(user_id) REFERENCES users (user_id)
                )
                """
            )
        )
        conn.execute(text("CREATE INDEX ix_worldbook_user_id ON worldbook (user_id)"))
        conn.execute(text("CREATE INDEX ix_worldbook_worldbook_id ON worldbook (worldbook_id)"))
        conn.execute(text("CREATE INDEX ix_worldbook_entry_id ON worldbook (entry_id)"))
        conn.execute(text("CREATE INDEX ix_worldbook_category ON worldbook (category)"))

        for row in rows:
            conn.execute(
                text(
                    """
                    INSERT INTO worldbook (
                        id, user_id, worldbook_id, entry_id, category, tags, title, content,
                        importance, canonical, meta_json, created_at, updated_at
                    ) VALUES (
                        :id, :user_id, :worldbook_id, :entry_id, :category, :tags, :title, :content,
                        :importance, :canonical, :meta_json, :created_at, :updated_at
                    )
                    """
                ),
                {
                    "id": row["id"],
                    "user_id": row.get("user_id"),
                    "worldbook_id": assigned_ids[row["entry_id"]],
                    "entry_id": row["entry_id"],
                    "category": row.get("category"),
                    "tags": row.get("tags"),
                    "title": row["title"],
                    "content": row["content"],
                    "importance": row.get("importance"),
                    "canonical": row.get("canonical"),
                    "meta_json": row.get("meta_json"),
                    "created_at": row.get("created_at"),
                    "updated_at": row.get("updated_at"),
                },
            )

        conn.execute(text("DROP TABLE worldbook_legacy"))
        conn.execute(text("PRAGMA foreign_keys=ON"))
        print(f"rebuilt worldbook: {len(rows)} rows")


def _rebuild_worldbook_embeddings() -> None:
    if not _table_exists("worldbook_embeddings"):
        print("skip worldbook_embeddings rebuild: table missing")
        return
    existing_columns = _columns("worldbook_embeddings")
    if existing_columns[:4] == ["id", "user_id", "worldbook_id", "entry_id"]:
        print("skip worldbook_embeddings rebuild")
        return

    with engine.begin() as conn:
        rows = conn.execute(text("SELECT * FROM worldbook_embeddings")).mappings().all()
        scope_rows = conn.execute(text("SELECT entry_id, user_id, worldbook_id FROM worldbook")).mappings().all()
        scope_map = {
            row["entry_id"]: {
                "user_id": row.get("user_id"),
                "worldbook_id": row.get("worldbook_id") or _generate_worldbook_id(),
            }
            for row in scope_rows
        }

        conn.execute(text("PRAGMA foreign_keys=OFF"))
        conn.execute(text("ALTER TABLE worldbook_embeddings RENAME TO worldbook_embeddings_legacy"))
        conn.execute(
            text(
                """
                CREATE TABLE worldbook_embeddings (
                    id INTEGER PRIMARY KEY,
                    user_id VARCHAR(32),
                    worldbook_id VARCHAR(8) NOT NULL,
                    entry_id VARCHAR NOT NULL,
                    embedding_json TEXT NOT NULL,
                    content_hash VARCHAR NOT NULL,
                    embedding_model VARCHAR NOT NULL,
                    dimension INTEGER NOT NULL,
                    created_at DATETIME,
                    updated_at DATETIME,
                    FOREIGN KEY(user_id) REFERENCES users (user_id),
                    FOREIGN KEY(entry_id) REFERENCES worldbook (entry_id)
                )
                """
            )
        )
        conn.execute(text("CREATE INDEX ix_worldbook_embeddings_user_id ON worldbook_embeddings (user_id)"))
        conn.execute(text("CREATE INDEX ix_worldbook_embeddings_worldbook_id ON worldbook_embeddings (worldbook_id)"))
        conn.execute(text("CREATE INDEX ix_worldbook_embeddings_entry_id ON worldbook_embeddings (entry_id)"))
        conn.execute(text("CREATE INDEX ix_worldbook_embeddings_content_hash ON worldbook_embeddings (content_hash)"))

        for row in rows:
            scope = scope_map.get(row["entry_id"], {"user_id": None, "worldbook_id": _generate_worldbook_id()})
            conn.execute(
                text(
                    """
                    INSERT INTO worldbook_embeddings (
                        id, user_id, worldbook_id, entry_id, embedding_json, content_hash,
                        embedding_model, dimension, created_at, updated_at
                    ) VALUES (
                        :id, :user_id, :worldbook_id, :entry_id, :embedding_json, :content_hash,
                        :embedding_model, :dimension, :created_at, :updated_at
                    )
                    """
                ),
                {
                    "id": row["id"],
                    "user_id": scope["user_id"],
                    "worldbook_id": scope["worldbook_id"],
                    "entry_id": row["entry_id"],
                    "embedding_json": row["embedding_json"],
                    "content_hash": row["content_hash"],
                    "embedding_model": row["embedding_model"],
                    "dimension": row["dimension"],
                    "created_at": row.get("created_at"),
                    "updated_at": row.get("updated_at"),
                },
            )

        conn.execute(text("DROP TABLE worldbook_embeddings_legacy"))
        conn.execute(text("PRAGMA foreign_keys=ON"))
        print(f"rebuilt worldbook_embeddings: {len(rows)} rows")


def run_migration() -> None:
    if engine.dialect.name != "sqlite":
        print(f"skip worldbook isolation migration for dialect={engine.dialect.name}")
        return
    print("start worldbook isolation migration")
    _rebuild_worldbook()
    _rebuild_worldbook_embeddings()
    print("worldbook isolation migration complete")


if __name__ == "__main__":
    run_migration()
