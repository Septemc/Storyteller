"""
[新增] 角色字段迁移脚本
将所有 data_json 中的数据重新分配到各个分类字段 (basic_json, knowledge_json 等)
运行方式: python scripts/migrate_character_fields.py
"""
import json
import sys
from pathlib import Path

# 添加 backend 到 Python 路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.db.base import SessionLocal, engine
from backend.db import models


def extract_and_assign_fields(data: dict) -> dict:
    """
    从 data_json 中识别并提取各个分类字段
    支持多种数据结构：
    - { "tab_basic": {...}, "tab_knowledge": {...}, ... }
    - { "basic": {...}, "knowledge": {...}, ... }
    - { "f_name": ..., "f_tags": ..., ... } (直接的字段值)
    """
    result = {
        "basic_json": json.dumps({}, ensure_ascii=False),
        "knowledge_json": json.dumps({}, ensure_ascii=False),
        "secrets_json": json.dumps({}, ensure_ascii=False),
        "attributes_json": json.dumps({}, ensure_ascii=False),
        "relations_json": json.dumps({}, ensure_ascii=False),
        "equipment_json": json.dumps({}, ensure_ascii=False),
        "items_json": json.dumps({}, ensure_ascii=False),
        "skills_json": json.dumps({}, ensure_ascii=False),
        "fortune_json": json.dumps({}, ensure_ascii=False),
    }
    
    field_patterns = {
        "basic_json": ["tab_basic", "basic"],
        "knowledge_json": ["tab_knowledge", "knowledge"],
        "secrets_json": ["tab_secrets", "secrets"],
        "attributes_json": ["tab_attributes", "attributes"],
        "relations_json": ["tab_relations", "relations"],
        "equipment_json": ["tab_equipment", "equipment"],
        "items_json": ["tab_items", "items"],
        "skills_json": ["tab_skills", "skills"],
        "fortune_json": ["tab_fortune", "fortune"],
    }
    
    # 尝试从 tab_xxx 或 xxx 字段提取
    for db_field, patterns in field_patterns.items():
        for pattern in patterns:
            if pattern in data:
                value = data[pattern]
                if value is None:
                    value = {}
                result[db_field] = json.dumps(value, ensure_ascii=False)
                break
    
    # 如果 data 本身看起来像一个 tab 对象（包含 f_* 字段），绑定到 basic
    if result["basic_json"] == json.dumps({}, ensure_ascii=False) and any(k.startswith("f_") for k in data.keys()):
        result["basic_json"] = json.dumps(data, ensure_ascii=False)
    
    return result


def migrate():
    """执行迁移"""
    db = SessionLocal()
    try:
        characters = db.query(models.Character).all()
        total = len(characters)
        updated = 0
        failed = 0
        
        print(f"[迁移开始] 发现 {total} 个角色")
        
        for idx, ch in enumerate(characters, 1):
            try:
                # 解析 data_json
                if not ch.data_json:
                    print(f"  [{idx}/{total}] ⚠ {ch.character_id} - data_json 为空，跳过")
                    continue
                
                try:
                    data = json.loads(ch.data_json)
                except json.JSONDecodeError as e:
                    print(f"  [{idx}/{total}] ✗ {ch.character_id} - JSON 解析失败: {e}")
                    failed += 1
                    continue
                
                # 提取并分配字段
                fields = extract_and_assign_fields(data)
                
                # 检查是否有任何变更
                changed = False
                for field, value in fields.items():
                    current = getattr(ch, field, None)
                    if current != value:
                        setattr(ch, field, value)
                        changed = True
                
                if changed:
                    print(f"  [{idx}/{total}] ✓ {ch.character_id} - 字段已更新")
                    updated += 1
                else:
                    print(f"  [{idx}/{total}] - {ch.character_id} - 无变更")
            
            except Exception as e:
                print(f"  [{idx}/{total}] ✗ {ch.character_id} - 迁移失败: {e}")
                failed += 1
                continue
        
        # 提交更改
        db.commit()
        print(f"\n[迁移完成]")
        print(f"  总数: {total}")
        print(f"  更新: {updated}")
        print(f"  失败: {failed}")
        
    except Exception as e:
        db.rollback()
        print(f"[错误] 迁移过程中出现错误: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    migrate()
