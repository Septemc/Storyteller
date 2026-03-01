"""
数据库迁移脚本：为 presets 和 regex_profiles 表添加 is_default 字段
"""
import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from sqlalchemy import text
from backend.db.base import engine, SessionLocal
from backend.db.models import Base, DBPreset, DBRegexProfile


def migrate_presets(db):
    print("\n--- 迁移 presets 表 ---")
    
    try:
        with engine.connect() as conn:
            result = conn.execute(text("PRAGMA table_info(presets)"))
            columns = [row[1] for row in result.fetchall()]
            
            if 'is_default' not in columns:
                print("添加 is_default 字段...")
                conn.execute(text("ALTER TABLE presets ADD COLUMN is_default BOOLEAN DEFAULT 0"))
                conn.commit()
                print("is_default 字段添加成功")
            else:
                print("is_default 字段已存在")
    except Exception as e:
        print(f"迁移警告: {e}")
    
    default_preset = db.query(DBPreset).filter(DBPreset.id == "preset_default").first()
    
    if default_preset:
        default_preset.is_default = True
        print(f"已将 {default_preset.name} 标记为默认预设")
    else:
        default_preset_path = Path(__file__).parent.parent.parent / "data" / "default_preset.json"
        if default_preset_path.exists():
            with open(default_preset_path, "r", encoding="utf-8") as f:
                preset_data = json.load(f)
            
            new_default = DBPreset(
                id=preset_data.get("id", "preset_default"),
                name=preset_data.get("name", "默认预设"),
                version=preset_data.get("version", 1),
                is_active=True,
                is_default=True,
                config_json=json.dumps(preset_data, ensure_ascii=False)
            )
            db.add(new_default)
            print("已从文件导入默认预设")


def migrate_regex_profiles(db):
    print("\n--- 迁移 regex_profiles 表 ---")
    
    try:
        with engine.connect() as conn:
            result = conn.execute(text("PRAGMA table_info(regex_profiles)"))
            columns = [row[1] for row in result.fetchall()]
            
            if 'is_default' not in columns:
                print("添加 is_default 字段...")
                conn.execute(text("ALTER TABLE regex_profiles ADD COLUMN is_default BOOLEAN DEFAULT 0"))
                conn.commit()
                print("is_default 字段添加成功")
            else:
                print("is_default 字段已存在")
    except Exception as e:
        print(f"迁移警告: {e}")
    
    default_regex = db.query(DBRegexProfile).filter(DBRegexProfile.id == "regex_default").first()
    
    if default_regex:
        default_regex.is_default = True
        print(f"已将 {default_regex.name} 标记为默认正则配置")
    else:
        default_regex_path = Path(__file__).parent.parent.parent / "data" / "default_regex.json"
        if default_regex_path.exists():
            with open(default_regex_path, "r", encoding="utf-8") as f:
                regex_data = json.load(f)
            
            new_default = DBRegexProfile(
                id=regex_data.get("id", "regex_default"),
                name=regex_data.get("name", "默认正则化"),
                version=regex_data.get("version", 1),
                is_active=True,
                is_default=True,
                config_json=json.dumps(regex_data, ensure_ascii=False)
            )
            db.add(new_default)
            print("已从文件导入默认正则配置")


def migrate():
    print("=" * 60)
    print("开始迁移...")
    print("=" * 60)
    
    db = SessionLocal()
    try:
        migrate_presets(db)
        migrate_regex_profiles(db)
        db.commit()
        print("\n迁移完成!")
    except Exception as e:
        print(f"迁移错误: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    migrate()
