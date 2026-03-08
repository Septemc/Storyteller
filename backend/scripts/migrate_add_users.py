"""
数据库迁移脚本：添加用户系统支持

功能：
1. 创建 users 和 user_relationships 表
2. 为所有业务表添加 user_id 字段
3. 创建默认管理员账户
4. 将现有数据关联到管理员账户
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from sqlalchemy import text, inspect
from backend.db.base import engine, SessionLocal
from backend.db.models import Base, User, UserRole
from backend.core.auth import get_password_hash, create_admin_user


def table_exists(table_name: str) -> bool:
    inspector = inspect(engine)
    return table_name in inspector.get_table_names()


def column_exists(table_name: str, column_name: str) -> bool:
    inspector = inspect(engine)
    if table_name not in inspector.get_table_names():
        return False
    columns = [col['name'] for col in inspector.get_columns(table_name)]
    return column_name in columns


def migrate_database():
    print("=" * 60)
    print("开始数据库迁移：添加用户系统支持")
    print("=" * 60)
    
    db = SessionLocal()
    
    try:
        print("\n[步骤1] 创建 users 表...")
        if not table_exists("users"):
            User.__table__.create(engine, checkfirst=True)
            print("  ✅ users 表创建成功")
        else:
            print("  ⏭️ users 表已存在，跳过")
        
        print("\n[步骤2] 创建默认管理员账户...")
        admin = create_admin_user(db, username="admin", password="admin123")
        admin_id = admin.id
        print(f"  ✅ 管理员账户已就绪: {admin.username} (ID: {admin_id})")
        
        business_tables = [
            "worldbook_entries",
            "dungeons",
            "character_templates",
            "characters",
            "global_settings",
            "story_segments",
            "session_state",
            "presets",
            "llm_configs",
            "regex_profiles",
        ]
        
        print("\n[步骤3] 为业务表添加 user_id 字段...")
        with engine.connect() as conn:
            for table_name in business_tables:
                if table_exists(table_name):
                    if not column_exists(table_name, "user_id"):
                        try:
                            conn.execute(text(f"""
                                ALTER TABLE {table_name} 
                                ADD COLUMN user_id INTEGER REFERENCES users(id)
                            """))
                            conn.commit()
                            print(f"  ✅ {table_name}: 添加 user_id 字段")
                        except Exception as e:
                            print(f"  ⚠️ {table_name}: 添加字段失败 - {e}")
                    else:
                        print(f"  ⏭️ {table_name}: user_id 字段已存在")
                else:
                    print(f"  ⏭️ {table_name}: 表不存在")
        
        print("\n[步骤4] 将现有数据关联到管理员账户...")
        with engine.connect() as conn:
            for table_name in business_tables:
                if table_exists(table_name) and column_exists(table_name, "user_id"):
                    try:
                        result = conn.execute(text(f"""
                            UPDATE {table_name} 
                            SET user_id = :admin_id 
                            WHERE user_id IS NULL
                        """), {"admin_id": admin_id})
                        conn.commit()
                        if result.rowcount > 0:
                            print(f"  ✅ {table_name}: 更新 {result.rowcount} 条记录")
                        else:
                            print(f"  ⏭️ {table_name}: 无需更新")
                    except Exception as e:
                        print(f"  ⚠️ {table_name}: 更新失败 - {e}")
        
        print("\n[步骤5] 创建 user_relationships 表...")
        from backend.db.models import UserRelationship
        if not table_exists("user_relationships"):
            UserRelationship.__table__.create(engine, checkfirst=True)
            print("  ✅ user_relationships 表创建成功")
        else:
            print("  ⏭️ user_relationships 表已存在，跳过")
        
        print("\n" + "=" * 60)
        print("✅ 数据库迁移完成！")
        print("=" * 60)
        print(f"\n默认管理员账户信息：")
        print(f"  用户名: admin")
        print(f"  密码: admin123")
        print(f"  ⚠️ 请登录后立即修改密码！")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ 迁移失败: {e}")
        raise
    finally:
        db.close()


def rollback_migration():
    print("=" * 60)
    print("回滚数据库迁移：移除用户系统支持")
    print("=" * 60)
    
    business_tables = [
        "worldbook_entries",
        "dungeons",
        "character_templates",
        "characters",
        "global_settings",
        "story_segments",
        "session_state",
        "presets",
        "llm_configs",
        "regex_profiles",
    ]
    
    with engine.connect() as conn:
        print("\n[步骤1] 移除业务表的 user_id 字段...")
        for table_name in business_tables:
            if table_exists(table_name) and column_exists(table_name, "user_id"):
                try:
                    conn.execute(text(f"ALTER TABLE {table_name} DROP COLUMN user_id"))
                    conn.commit()
                    print(f"  ✅ {table_name}: 移除 user_id 字段")
                except Exception as e:
                    print(f"  ⚠️ {table_name}: 移除失败 - {e}")
        
        print("\n[步骤2] 删除用户相关表...")
        if table_exists("user_relationships"):
            try:
                conn.execute(text("DROP TABLE user_relationships"))
                conn.commit()
                print("  ✅ user_relationships 表已删除")
            except Exception as e:
                print(f"  ⚠️ 删除 user_relationships 表失败 - {e}")
        
        if table_exists("users"):
            try:
                conn.execute(text("DROP TABLE users"))
                conn.commit()
                print("  ✅ users 表已删除")
            except Exception as e:
                print(f"  ⚠️ 删除 users 表失败 - {e}")
    
    print("\n" + "=" * 60)
    print("✅ 回滚完成！")
    print("=" * 60)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="数据库迁移脚本")
    parser.add_argument("--rollback", action="store_true", help="回滚迁移")
    args = parser.parse_args()
    
    if args.rollback:
        rollback_migration()
    else:
        migrate_database()
