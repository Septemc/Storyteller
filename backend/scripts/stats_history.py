"""
历史数据统计脚本
用于统计story_segments表中历史数据的字数并更新到数据库

使用方法:
    python -m backend.scripts.stats_history
"""

import re
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from sqlalchemy.orm import Session
from backend.db.base import SessionLocal
from backend.db import models


def extract_body_text(text: str) -> str:
    """
    提取<正文部分>标签内的文字
    如果找不到标签，返回空字符串
    """
    if not text:
        return ""
    
    body_match = re.search(r'<正文部分>(.*?)</正文部分>', text, re.DOTALL)
    if body_match:
        return body_match.group(1)
    return ""


def count_words(text: str) -> int:
    """
    统计文字数量
    """
    if not text:
        return 0
    return len(text)


def update_history_stats():
    """
    统计历史数据并更新数据库
    """
    db: Session = SessionLocal()
    
    try:
        print("开始统计历史数据...")
        
        segments = db.query(models.StorySegment).order_by(
            models.StorySegment.session_id,
            models.StorySegment.order_index
        ).all()
        
        session_cumulative = {}
        updated_count = 0
        
        for seg in segments:
            body_text = extract_body_text(seg.text)
            word_count = count_words(body_text)
            
            session_id = seg.session_id
            
            cumulative = session_cumulative.get(session_id, 0)
            cumulative += word_count
            session_cumulative[session_id] = cumulative
            
            seg.paragraph_word_count = word_count
            seg.cumulative_word_count = cumulative
            seg.frontend_duration = seg.frontend_duration or 0.0
            seg.backend_duration = seg.backend_duration or 0.0
            
            updated_count += 1
            
            if updated_count % 100 == 0:
                print(f"已处理 {updated_count} 条记录...")
        
        db.commit()
        
        print(f"\n统计完成!")
        print(f"共更新 {updated_count} 条记录")
        
        for session_id, total in session_cumulative.items():
            print(f"  会话 {session_id}: 累计字数 {total}")
        
        session_state = db.query(models.SessionState).all()
        for state in session_state:
            session_id = state.session_id
            if session_id in session_cumulative:
                state.total_word_count = session_cumulative[session_id]
        
        db.commit()
        print("\n会话总字数已更新")
        
    except Exception as e:
        print(f"统计过程中出错: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    update_history_stats()
