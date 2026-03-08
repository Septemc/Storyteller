#!/usr/bin/env python3
"""
[迁移脚本] 添加 Script 表和扩展 SessionState 表

功能：
1. 创建 scripts 表 - 存储脚本元数据
2. 添加 current_script_id 列到 session_state 表（如果不存在）

用法：
  python scripts/migrate_add_script_table.py
"""

import sys
import json
from pathlib import Path
from datetime import datetime

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import text, inspect
from backend.db.base import engine, Base
from backend.db import models

def migrate():
    """执行迁移"""
    print("=" * 60)
    print("[迁移] 添加 Script 表和扩展 SessionState")
    print("=" * 60)
    
    with engine.connect() as conn:
        inspector = inspect(engine)
        existing_tables = inspector.get_table_names()
        
        # 1. 创建 scripts 表（如果不存在）
        if "scripts" not in existing_tables:
            print("\n✓ 创建 scripts 表...")
            models.Base.metadata.tables["scripts"].create(engine, checkfirst=True)
            print("  ✓ scripts 表创建成功")
        else:
            print("\n• scripts 表已存在，跳过创建")
        
        # 2. 检查并添加 current_script_id 列（如果不存在）
        if "session_state" in existing_tables:
            columns = {col["name"] for col in inspector.get_columns("session_state")}
            
            if "current_script_id" not in columns:
                print("\n✓ 向 session_state 表添加 current_script_id 列...")
                conn.execute(
                    text('ALTER TABLE session_state ADD COLUMN current_script_id VARCHAR')
                )
                conn.commit()
                print("  ✓ current_script_id 列添加成功")
            else:
                print("\n• current_script_id 列已存在，跳过添加")
        else:
            print("\n✗ session_state 表不存在！")
            return False
    
    print("\n" + "=" * 60)
    print("✓ 迁移完成！")
    print("=" * 60)
    return True


if __name__ == "__main__":
    try:
        success = migrate()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n✗ 迁移失败: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)
