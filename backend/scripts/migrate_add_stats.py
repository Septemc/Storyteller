"""
数据库迁移脚本：添加统计字段到story_segments表

使用方法:
    python -m backend.scripts.migrate_add_stats
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from sqlalchemy import text
from backend.db.base import engine


def migrate():
    """
    添加统计字段到story_segments表
    """
    print("开始数据库迁移...")
    
    with engine.connect() as conn:
        try:
            result = conn.execute(text("PRAGMA table_info(story_segments)"))
            columns = [row[1] for row in result.fetchall()]
            
            if 'paragraph_word_count' not in columns:
                print("添加 paragraph_word_count 字段...")
                conn.execute(text("ALTER TABLE story_segments ADD COLUMN paragraph_word_count INTEGER DEFAULT 0"))
                print("  完成")
            else:
                print("paragraph_word_count 字段已存在，跳过")
            
            if 'cumulative_word_count' not in columns:
                print("添加 cumulative_word_count 字段...")
                conn.execute(text("ALTER TABLE story_segments ADD COLUMN cumulative_word_count INTEGER DEFAULT 0"))
                print("  完成")
            else:
                print("cumulative_word_count 字段已存在，跳过")
            
            if 'frontend_duration' not in columns:
                print("添加 frontend_duration 字段...")
                conn.execute(text("ALTER TABLE story_segments ADD COLUMN frontend_duration REAL DEFAULT 0.0"))
                print("  完成")
            else:
                print("frontend_duration 字段已存在，跳过")
            
            if 'backend_duration' not in columns:
                print("添加 backend_duration 字段...")
                conn.execute(text("ALTER TABLE story_segments ADD COLUMN backend_duration REAL DEFAULT 0.0"))
                print("  完成")
            else:
                print("backend_duration 字段已存在，跳过")
            
            conn.commit()
            print("\n迁移完成!")
            
        except Exception as e:
            print(f"迁移失败: {e}")
            raise


if __name__ == "__main__":
    migrate()
