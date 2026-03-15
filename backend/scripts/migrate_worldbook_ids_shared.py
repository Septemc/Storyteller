import sys
import uuid
from pathlib import Path

from sqlalchemy import inspect, text

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from backend.db.base import engine  # noqa: E402


def table_exists(table_name: str) -> bool:
    return table_name in inspect(engine).get_table_names()


def columns(table_name: str):
    return [column["name"] for column in inspect(engine).get_columns(table_name)] if table_exists(table_name) else []


def generate_worldbook_id() -> str:
    return f"W{uuid.uuid4().hex[:7]}"


def execute(sql: str):
    return text(sql)
