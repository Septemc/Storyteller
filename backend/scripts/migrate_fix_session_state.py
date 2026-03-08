"""
数据库迁移脚本：修复session_state表结构

问题：session_state表缺少current_script_id列
解决方案：添加缺失的列
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from sqlalchemy import text, inspect
from backend.db.base import engine, SessionLocal


def table_exists(table_name: str) -> bool:
    inspector = inspect(engine)
    return table_name in inspector.get_table_names()


def column_exists(table_name: str, column_name: str) -> bool:
    inspector = inspect(engine)
    if table_name not in inspector.get_table_names():
        return False
    columns = [col['name'] for col in inspector.get_columns(table_name)]
    return column_name in columns


def migrate_session_state_table():
    """修复session_state表结构"""
    
    print("=" * 60)
    print("开始数据库迁移：修复session_state表结构")
    print("=" * 60)
    
    db = SessionLocal()
    
    try:
        # 检查表是否存在
        if not table_exists("session_state"):
            print("❌ session_state 表不存在，需要重新创建")
            return False
        
        # 检查缺失的列
        missing_columns = []
        
        if not column_exists("session_state", "current_script_id"):
            missing_columns.append("current_script_id")
        
        if not missing_columns:
            print("✅ session_state 表结构完整，无需迁移")
            return True
        
        print(f"\n发现缺失的列: {missing_columns}")
        
        # 添加缺失的列
        for column in missing_columns:
            print(f"\n[添加列] {column}...")
            
            if column == "current_script_id":
                # 添加 current_script_id 列
                db.execute(text("ALTER TABLE session_state ADD COLUMN current_script_id VARCHAR"))
                print("  ✅ 添加 current_script_id 列成功")
        
        db.commit()
        print("\n✅ session_state 表结构修复完成！")
        
        # 验证修复结果
        print("\n[验证] 检查表结构...")
        inspector = inspect(engine)
        columns = [col['name'] for col in inspector.get_columns("session_state")]
        print(f"  session_state 表现有列: {columns}")
        
        # 检查是否所有必需的列都存在
        required_columns = ["current_script_id"]
        for col in required_columns:
            if col in columns:
                print(f"  ✅ {col} 列存在")
            else:
                print(f"  ❌ {col} 列缺失")
        
        return True
        
    except Exception as e:
        print(f"❌ 迁移失败: {e}")
        db.rollback()
        return False
    finally:
        db.close()


def test_session_state_query():
    """测试session_state查询是否正常"""
    
    print("\n[测试] 测试session_state查询...")
    
    db = SessionLocal()
    
    try:
        # 创建一个测试会话
        test_session_id = "migration_test_session_" + str(hash("test"))
        
        # 检查是否能正常查询
        result = db.execute(
            text("SELECT * FROM session_state WHERE session_id = :session_id"),
            {"session_id": test_session_id}
        ).fetchone()
        
        if result:
            print("  ✅ session_state 查询正常")
            print(f"  查询结果: {result}")
        else:
            print("  ⚠️  未找到测试会话（正常，因为会话不存在）")
        
        # 测试插入新会话
        insert_result = db.execute(
            text("""
                INSERT INTO session_state (session_id, current_script_id, current_dungeon_id, current_node_id, total_word_count)
                VALUES (:session_id, :script_id, :dungeon_id, :node_id, :word_count)
            """),
            {
                "session_id": test_session_id,
                "script_id": "test_script",
                "dungeon_id": "test_dungeon",
                "node_id": "test_node",
                "word_count": 0
            }
        )
        
        db.commit()
        print("  ✅ session_state 插入操作正常")
        
        # 清理测试数据
        db.execute(
            text("DELETE FROM session_state WHERE session_id = :session_id"),
            {"session_id": test_session_id}
        )
        db.commit()
        print("  ✅ 测试数据清理完成")
        
        return True
        
    except Exception as e:
        print(f"  ❌ session_state 测试失败: {e}")
        db.rollback()
        return False
    finally:
        db.close()


if __name__ == "__main__":
    # 执行迁移
    migration_success = migrate_session_state_table()
    
    if migration_success:
        # 测试修复结果
        test_success = test_session_state_query()
        
        if test_success:
            print("\n🎉 数据库迁移和测试完成！")
            print("  现在可以重新测试'生成下一段'功能")
        else:
            print("\n⚠️  迁移完成但测试失败")
            print("  请检查数据库连接和表结构")
    else:
        print("\n❌ 数据库迁移失败")
        print("  请检查数据库连接和权限")