"""
数据库会话内容提取脚本

功能：
1. 从story_segments表的text字段中提取以下标识符包裹的内容：
   - <思考过程>...</思考过程>
   - <正文部分>...</正文部分>
   - <内容总结>...</内容总结>
   - <行动选项>...</行动选项>
2. 将提取结果存储到对应的新字段中
3. 生成执行日志

使用方法：
    python backend/scripts/extract_content_fields.py
"""

import re
import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from sqlalchemy import text
from backend.db.base import SessionLocal
from backend.db import models


def extract_tag_content(text: str, tag_name: str) -> str:
    pattern = rf'<{tag_name}>(.*?)</{tag_name}>'
    match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
    if match:
        return match.group(1).strip()
    return None


def extract_content_fields(text: str) -> dict:
    if not text:
        return {
            'content_thinking': None,
            'content_story': None,
            'content_summary': None,
            'content_actions': None,
        }
    
    return {
        'content_thinking': extract_tag_content(text, '思考过程'),
        'content_story': extract_tag_content(text, '正文部分'),
        'content_summary': extract_tag_content(text, '内容总结'),
        'content_actions': extract_tag_content(text, '行动选项'),
    }


def run_migration(db):
    print("=" * 60)
    print("检查并添加新字段...")
    
    try:
        db.execute(text("""
            ALTER TABLE story_segments 
            ADD COLUMN content_thinking TEXT
        """))
        print("  - 添加 content_thinking 字段")
    except Exception as e:
        if "duplicate column" in str(e).lower() or "already exists" in str(e).lower():
            print("  - content_thinking 字段已存在")
        else:
            print(f"  - 添加 content_thinking 字段时出错: {e}")
    
    try:
        db.execute(text("""
            ALTER TABLE story_segments 
            ADD COLUMN content_story TEXT
        """))
        print("  - 添加 content_story 字段")
    except Exception as e:
        if "duplicate column" in str(e).lower() or "already exists" in str(e).lower():
            print("  - content_story 字段已存在")
        else:
            print(f"  - 添加 content_story 字段时出错: {e}")
    
    try:
        db.execute(text("""
            ALTER TABLE story_segments 
            ADD COLUMN content_summary TEXT
        """))
        print("  - 添加 content_summary 字段")
    except Exception as e:
        if "duplicate column" in str(e).lower() or "already exists" in str(e).lower():
            print("  - content_summary 字段已存在")
        else:
            print(f"  - 添加 content_summary 字段时出错: {e}")
    
    try:
        db.execute(text("""
            ALTER TABLE story_segments 
            ADD COLUMN content_actions TEXT
        """))
        print("  - 添加 content_actions 字段")
    except Exception as e:
        if "duplicate column" in str(e).lower() or "already exists" in str(e).lower():
            print("  - content_actions 字段已存在")
        else:
            print(f"  - 添加 content_actions 字段时出错: {e}")
    
    db.commit()
    print("字段检查完成！\n")


def main():
    print("=" * 60)
    print("数据库会话内容提取脚本")
    print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    db = SessionLocal()
    
    try:
        run_migration(db)
        
        print("=" * 60)
        print("开始提取内容...")
        
        segments = db.query(models.StorySegment).order_by(models.StorySegment.order_index).all()
        total_count = len(segments)
        success_count = 0
        skip_count = 0
        error_ids = []
        
        print(f"共找到 {total_count} 条记录")
        print("-" * 60)
        
        for i, seg in enumerate(segments, 1):
            try:
                if seg.content_summary and seg.content_summary.strip():
                    skip_count += 1
                    if i % 50 == 0 or i == total_count:
                        print(f"进度: {i}/{total_count} - 跳过已处理记录")
                    continue
                
                extracted = extract_content_fields(seg.text)
                
                seg.content_thinking = extracted['content_thinking']
                seg.content_story = extracted['content_story']
                seg.content_summary = extracted['content_summary']
                seg.content_actions = extracted['content_actions']
                
                success_count += 1
                
                if i % 50 == 0 or i == total_count:
                    print(f"进度: {i}/{total_count} - 已处理 {success_count} 条，跳过 {skip_count} 条")
                
            except Exception as e:
                error_ids.append(seg.segment_id)
                print(f"  [错误] segment_id={seg.segment_id}: {e}")
        
        db.commit()
        
        print("\n" + "=" * 60)
        print("提取完成！")
        print(f"结束时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("-" * 60)
        print(f"总记录数: {total_count}")
        print(f"成功处理: {success_count}")
        print(f"跳过记录: {skip_count}")
        print(f"失败记录: {len(error_ids)}")
        
        if error_ids:
            print("\n失败记录ID:")
            for eid in error_ids[:10]:
                print(f"  - {eid}")
            if len(error_ids) > 10:
                print(f"  ... 还有 {len(error_ids) - 10} 条")
        
        print("=" * 60)
        
    except Exception as e:
        print(f"\n[严重错误] {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
