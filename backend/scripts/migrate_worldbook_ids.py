from backend.scripts.migrate_worldbook_embeddings import rebuild_worldbook_embeddings
from backend.scripts.migrate_worldbook_ids_shared import engine
from backend.scripts.migrate_worldbook_rows import rebuild_worldbook


def run_migration() -> None:
    if engine.dialect.name != "sqlite":
        print(f"skip worldbook isolation migration for dialect={engine.dialect.name}")
        return
    print("start worldbook isolation migration")
    rebuild_worldbook()
    rebuild_worldbook_embeddings()
    print("worldbook isolation migration complete")


if __name__ == "__main__":
    run_migration()
