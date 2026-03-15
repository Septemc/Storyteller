from __future__ import annotations

from sqlalchemy import inspect

from ..db.base import engine
from ..db.models.narrative import CharacterTemplate

EXPECTED = [
    "id",
    "user_id",
    "session_id",
    "template_id",
    "template_name",
    "template_json",
    "is_active",
    "created_at",
    "updated_at",
]


def rebuild_if_needed() -> None:
    inspector = inspect(engine)
    if "character_templates" not in inspector.get_table_names():
        CharacterTemplate.__table__.create(bind=engine, checkfirst=True)
        return
    columns = [column["name"] for column in inspector.get_columns("character_templates")]
    if columns != EXPECTED:
        CharacterTemplate.__table__.drop(bind=engine, checkfirst=True)
        CharacterTemplate.__table__.create(bind=engine, checkfirst=True)


if __name__ == "__main__":
    rebuild_if_needed()
