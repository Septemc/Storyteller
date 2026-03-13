"""
Migrate the local SQLite database into PostgreSQL.

Usage:
  python -m backend.scripts.migrate_sqlite_to_postgres
  python -m backend.scripts.migrate_sqlite_to_postgres --target-url postgresql+psycopg://user:pass@127.0.0.1:5433/st
  python -m backend.scripts.migrate_sqlite_to_postgres --truncate-target
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Iterable

from sqlalchemy import Integer, MetaData, create_engine, inspect, select, text
from sqlalchemy.engine import Engine

from backend.config import settings
from backend.db.models import Base


DEFAULT_SOURCE_URL = "sqlite:///./data/db.sqlite"
DEFAULT_BATCH_SIZE = 500


def build_engine(url: str) -> Engine:
    connect_args = {"check_same_thread": False} if url.startswith("sqlite") else {}
    return create_engine(url, connect_args=connect_args)


def chunked(items: list[dict], size: int) -> Iterable[list[dict]]:
    for index in range(0, len(items), size):
        yield items[index:index + size]


def ensure_postgres(url: str) -> None:
    if not url.startswith("postgresql"):
        raise ValueError(f"target database must be PostgreSQL, got: {url}")


def ensure_sqlite(url: str) -> None:
    if not url.startswith("sqlite"):
        raise ValueError(f"source database must be SQLite, got: {url}")


def truncate_target_tables(target_engine: Engine) -> None:
    if target_engine.dialect.name != "postgresql":
        return

    table_names = [table.name for table in reversed(Base.metadata.sorted_tables)]
    joined = ", ".join(f'"{name}"' for name in table_names)
    with target_engine.begin() as conn:
        conn.execute(text(f"TRUNCATE TABLE {joined} RESTART IDENTITY CASCADE"))


def reset_postgres_sequences(target_engine: Engine) -> None:
    if target_engine.dialect.name != "postgresql":
        return

    with target_engine.begin() as conn:
        for table in Base.metadata.sorted_tables:
            if "id" not in table.c:
                continue
            if not isinstance(table.c.id.type, Integer):
                continue
            conn.execute(
                text(
                    """
                    SELECT setval(
                        pg_get_serial_sequence(:table_name, 'id'),
                        COALESCE((SELECT MAX(id) FROM "{}"), 1),
                        (SELECT COUNT(*) > 0 FROM "{}")
                    )
                    """.format(table.name, table.name)
                ),
                {"table_name": table.name},
            )


def migrate_table(source_engine: Engine, target_engine: Engine, table_name: str, batch_size: int) -> int:
    source_metadata = MetaData()
    source_metadata.reflect(bind=source_engine, only=[table_name])
    source_table = source_metadata.tables[table_name]
    target_table = Base.metadata.tables[table_name]

    with source_engine.connect() as source_conn:
        rows = [dict(row) for row in source_conn.execute(select(source_table)).mappings()]

    if not rows:
        return 0

    with target_engine.begin() as target_conn:
        for batch in chunked(rows, batch_size):
            target_conn.execute(target_table.insert(), batch)

    return len(rows)


def migrate(source_url: str, target_url: str, truncate_target: bool, batch_size: int) -> None:
    ensure_sqlite(source_url)
    ensure_postgres(target_url)

    source_engine = build_engine(source_url)
    target_engine = build_engine(target_url)

    source_tables = set(inspect(source_engine).get_table_names())
    Base.metadata.create_all(bind=target_engine)

    if truncate_target:
        truncate_target_tables(target_engine)

    copied_counts: dict[str, int] = {}
    try:
        for table in Base.metadata.sorted_tables:
            if table.name not in source_tables:
                copied_counts[table.name] = 0
                continue
            copied_counts[table.name] = migrate_table(source_engine, target_engine, table.name, batch_size)

        reset_postgres_sequences(target_engine)
    finally:
        source_engine.dispose()
        target_engine.dispose()

    print("SQLite -> PostgreSQL migration complete")
    for table_name, count in copied_counts.items():
        print(f"  {table_name}: {count} rows")


def main() -> None:
    parser = argparse.ArgumentParser(description="Migrate Storyteller data from SQLite to PostgreSQL.")
    parser.add_argument("--source-url", default=DEFAULT_SOURCE_URL, help=f"SQLite source URL. Default: {DEFAULT_SOURCE_URL}")
    parser.add_argument(
        "--target-url",
        default=settings.resolved_database_url,
        help="PostgreSQL target URL. Defaults to NOVEL_DATABASE_URL / .env database_url",
    )
    parser.add_argument("--truncate-target", action="store_true", help="Truncate PostgreSQL tables before copying data.")
    parser.add_argument("--batch-size", type=int, default=DEFAULT_BATCH_SIZE, help=f"Insert batch size. Default: {DEFAULT_BATCH_SIZE}")
    args = parser.parse_args()

    migrate(
        source_url=args.source_url,
        target_url=args.target_url,
        truncate_target=args.truncate_target,
        batch_size=args.batch_size,
    )


if __name__ == "__main__":
    main()
