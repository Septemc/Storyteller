from backend.scripts.migrate_worldbook_ids_shared import columns, engine, execute, generate_worldbook_id, table_exists


def rebuild_worldbook_embeddings() -> None:
    if not table_exists("worldbook_embeddings"):
        print("skip worldbook_embeddings rebuild: table missing")
        return
    if columns("worldbook_embeddings")[:4] == ["id", "user_id", "worldbook_id", "entry_id"]:
        print("skip worldbook_embeddings rebuild")
        return
    with engine.begin() as conn:
        rows = conn.execute(execute("SELECT * FROM worldbook_embeddings")).mappings().all()
        scope_rows = conn.execute(execute("SELECT entry_id, user_id, worldbook_id FROM worldbook")).mappings().all()
        scope_map = {row["entry_id"]: {"user_id": row.get("user_id"), "worldbook_id": row.get("worldbook_id") or generate_worldbook_id()} for row in scope_rows}
        conn.execute(execute("PRAGMA foreign_keys=OFF"))
        conn.execute(execute("ALTER TABLE worldbook_embeddings RENAME TO worldbook_embeddings_legacy"))
        conn.execute(execute("CREATE TABLE worldbook_embeddings (id INTEGER PRIMARY KEY, user_id VARCHAR(32), worldbook_id VARCHAR(8) NOT NULL, entry_id VARCHAR NOT NULL, embedding_json TEXT NOT NULL, content_hash VARCHAR NOT NULL, embedding_model VARCHAR NOT NULL, dimension INTEGER NOT NULL, created_at DATETIME, updated_at DATETIME, FOREIGN KEY(user_id) REFERENCES users (user_id), FOREIGN KEY(entry_id) REFERENCES worldbook (entry_id))"))
        conn.execute(execute("CREATE INDEX ix_worldbook_embeddings_user_id ON worldbook_embeddings (user_id)"))
        conn.execute(execute("CREATE INDEX ix_worldbook_embeddings_worldbook_id ON worldbook_embeddings (worldbook_id)"))
        conn.execute(execute("CREATE INDEX ix_worldbook_embeddings_entry_id ON worldbook_embeddings (entry_id)"))
        conn.execute(execute("CREATE INDEX ix_worldbook_embeddings_content_hash ON worldbook_embeddings (content_hash)"))
        for row in rows:
            scope = scope_map.get(row["entry_id"], {"user_id": None, "worldbook_id": generate_worldbook_id()})
            conn.execute(execute("INSERT INTO worldbook_embeddings (id, user_id, worldbook_id, entry_id, embedding_json, content_hash, embedding_model, dimension, created_at, updated_at) VALUES (:id, :user_id, :worldbook_id, :entry_id, :embedding_json, :content_hash, :embedding_model, :dimension, :created_at, :updated_at)"), {"id": row["id"], "user_id": scope["user_id"], "worldbook_id": scope["worldbook_id"], "entry_id": row["entry_id"], "embedding_json": row["embedding_json"], "content_hash": row["content_hash"], "embedding_model": row["embedding_model"], "dimension": row["dimension"], "created_at": row.get("created_at"), "updated_at": row.get("updated_at")})
        conn.execute(execute("DROP TABLE worldbook_embeddings_legacy"))
        conn.execute(execute("PRAGMA foreign_keys=ON"))
        print(f"rebuilt worldbook_embeddings: {len(rows)} rows")
