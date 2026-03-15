from backend.scripts.migrate_worldbook_ids_shared import columns, engine, execute, generate_worldbook_id, table_exists


def rebuild_worldbook() -> None:
    if not table_exists("worldbook"):
        print("skip worldbook rebuild: table missing")
        return
    if columns("worldbook")[:4] == ["id", "user_id", "worldbook_id", "entry_id"]:
        print("skip worldbook rebuild")
        return
    with engine.begin() as conn:
        rows = conn.execute(execute("SELECT * FROM worldbook")).mappings().all()
        assigned_ids = {row["entry_id"]: row.get("worldbook_id") or generate_worldbook_id() for row in rows}
        conn.execute(execute("PRAGMA foreign_keys=OFF"))
        conn.execute(execute("ALTER TABLE worldbook RENAME TO worldbook_legacy"))
        conn.execute(execute("CREATE TABLE worldbook (id INTEGER PRIMARY KEY, user_id VARCHAR(32), worldbook_id VARCHAR(8) NOT NULL, entry_id VARCHAR NOT NULL UNIQUE, category VARCHAR, tags VARCHAR, title VARCHAR NOT NULL, content TEXT NOT NULL, importance FLOAT, canonical BOOLEAN, meta_json TEXT, created_at DATETIME, updated_at DATETIME, FOREIGN KEY(user_id) REFERENCES users (user_id))"))
        conn.execute(execute("CREATE INDEX ix_worldbook_user_id ON worldbook (user_id)"))
        conn.execute(execute("CREATE INDEX ix_worldbook_worldbook_id ON worldbook (worldbook_id)"))
        conn.execute(execute("CREATE INDEX ix_worldbook_entry_id ON worldbook (entry_id)"))
        conn.execute(execute("CREATE INDEX ix_worldbook_category ON worldbook (category)"))
        for row in rows:
            conn.execute(execute("INSERT INTO worldbook (id, user_id, worldbook_id, entry_id, category, tags, title, content, importance, canonical, meta_json, created_at, updated_at) VALUES (:id, :user_id, :worldbook_id, :entry_id, :category, :tags, :title, :content, :importance, :canonical, :meta_json, :created_at, :updated_at)"), {"id": row["id"], "user_id": row.get("user_id"), "worldbook_id": assigned_ids[row["entry_id"]], "entry_id": row["entry_id"], "category": row.get("category"), "tags": row.get("tags"), "title": row["title"], "content": row["content"], "importance": row.get("importance"), "canonical": row.get("canonical"), "meta_json": row.get("meta_json"), "created_at": row.get("created_at"), "updated_at": row.get("updated_at")})
        conn.execute(execute("DROP TABLE worldbook_legacy"))
        conn.execute(execute("PRAGMA foreign_keys=ON"))
        print(f"rebuilt worldbook: {len(rows)} rows")
