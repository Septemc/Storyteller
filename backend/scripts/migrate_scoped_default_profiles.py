"""
数据库迁移：默认配置 ID 作用域化

目的：
- 避免不同用户的默认 preset / regex 使用相同主键 ID 发生冲突
"""

import sys
from pathlib import Path

from typing import Optional

from sqlalchemy import inspect, text

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from backend.db.base import engine  # noqa: E402


def table_exists(table_name: str) -> bool:
    inspector = inspect(engine)
    return table_name in inspector.get_table_names()


def _scope_id(base_id: str, user_id: Optional[str]) -> str:
    if user_id:
        return f"{base_id}__{user_id}"
    return base_id


def migrate_default_ids(table_name: str, base_default_id: str) -> None:
    if not table_exists(table_name):
        print(f"⏭ {table_name} 表不存在，跳过")
        return

    with engine.begin() as conn:
        rows = conn.execute(
            text(f"SELECT id, user_id, is_default FROM {table_name} WHERE is_default = 1")
        ).mappings().all()
        if not rows:
            print(f"⏭ {table_name} 无默认行，跳过")
            return

        updated = 0
        deleted = 0
        for row in rows:
            row_id = row["id"]
            user_id = row["user_id"]
            target_id = _scope_id(base_default_id, user_id)

            # 只迁移 legacy 默认 ID 或与目标 ID 不一致的默认行
            if row_id == target_id:
                continue
            if row_id != base_default_id and not row_id.startswith(f"{base_default_id}__"):
                continue

            conflict = conn.execute(
                text(f"SELECT id FROM {table_name} WHERE id = :id AND id != :current_id"),
                {"id": target_id, "current_id": row_id},
            ).fetchone()
            if conflict:
                conn.execute(text(f"DELETE FROM {table_name} WHERE id = :id"), {"id": row_id})
                deleted += 1
                continue

            conn.execute(
                text(f"UPDATE {table_name} SET id = :new_id WHERE id = :old_id"),
                {"new_id": target_id, "old_id": row_id},
            )
            updated += 1

        print(f"✅ {table_name} 默认 ID 迁移完成: updated={updated}, deleted={deleted}")


def run_migration() -> None:
    print("=" * 60)
    print("开始执行默认配置 ID 作用域化迁移")
    print("=" * 60)

    migrate_default_ids("presets", "preset_default")
    migrate_default_ids("regexs", "regex_default")

    print("=" * 60)
    print("迁移完成")
    print("=" * 60)


if __name__ == "__main__":
    run_migration()
