"""
数据库迁移：第二轮用户隔离策略

内容：
1. 为 scripts 表补充 user_id 字段（如缺失）
2. 将 global_settings 的 legacy key=global 迁移为 key=global::{user_id|public}
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


def column_exists(table_name: str, column_name: str) -> bool:
    inspector = inspect(engine)
    if table_name not in inspector.get_table_names():
        return False
    columns = [col["name"] for col in inspector.get_columns(table_name)]
    return column_name in columns


def add_script_user_id_column() -> None:
    if not table_exists("scripts"):
        print("⏭ scripts 表不存在，跳过")
        return

    with engine.begin() as conn:
        if not column_exists("scripts", "user_id"):
            conn.execute(text("ALTER TABLE scripts ADD COLUMN user_id VARCHAR(32)"))
            print("✅ scripts.user_id 添加完成")
        else:
            print("⏭ scripts.user_id 已存在，跳过")

        # 兼容旧库：补充索引（SQLite IF NOT EXISTS 安全）
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_scripts_user_id ON scripts (user_id)"))
        print("✅ scripts.user_id 索引已确保存在")


def _target_settings_key(user_id: Optional[str]) -> str:
    return f"global::{user_id}" if user_id else "global::public"


def migrate_global_settings_keys() -> None:
    if not table_exists("global_settings"):
        print("⏭ global_settings 表不存在，跳过")
        return

    with engine.begin() as conn:
        rows = conn.execute(
            text("SELECT id, user_id, key, value_json FROM global_settings")
        ).mappings().all()

        if not rows:
            print("⏭ global_settings 无数据，跳过")
            return

        migrated = 0
        merged_deleted = 0
        for row in rows:
            row_id = row["id"]
            user_id = row["user_id"]
            key = row["key"]

            target_key = _target_settings_key(user_id)
            if key == target_key:
                continue
            if key != "global" and not key.startswith("global::"):
                continue

            conflict = conn.execute(
                text("SELECT id FROM global_settings WHERE key = :k AND id != :id"),
                {"k": target_key, "id": row_id},
            ).fetchone()
            if conflict:
                # 目标 key 已存在时，删除旧行，避免唯一键冲突
                conn.execute(text("DELETE FROM global_settings WHERE id = :id"), {"id": row_id})
                merged_deleted += 1
                continue

            conn.execute(
                text("UPDATE global_settings SET key = :k WHERE id = :id"),
                {"k": target_key, "id": row_id},
            )
            migrated += 1

        print(f"✅ global_settings key 迁移完成: updated={migrated}, merged_deleted={merged_deleted}")


def run_migration() -> None:
    print("=" * 60)
    print("开始执行第二轮用户隔离迁移")
    print("=" * 60)

    add_script_user_id_column()
    migrate_global_settings_keys()

    print("=" * 60)
    print("迁移完成")
    print("=" * 60)


if __name__ == "__main__":
    run_migration()
