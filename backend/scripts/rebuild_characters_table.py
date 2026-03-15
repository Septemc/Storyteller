from __future__ import annotations

from sqlalchemy import inspect

from ..db.base import engine
from ..db.models.narrative import Character

EXPECTED = [
    "id",
    "user_id",
    "session_id",
    "template_id",
    "character_id",
    "data_json",
    "created_at",
    "updated_at",
]


def rebuild_if_needed() -> None:
    inspector = inspect(engine)
    if "characters" not in inspector.get_table_names():
        Character.__table__.create(bind=engine, checkfirst=True)
        return
    columns = [column["name"] for column in inspector.get_columns("characters")]
    if columns != EXPECTED:
        Character.__table__.drop(bind=engine, checkfirst=True)
        Character.__table__.create(bind=engine, checkfirst=True)


if __name__ == "__main__":
    rebuild_if_needed()
