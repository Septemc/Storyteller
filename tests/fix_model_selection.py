#!/usr/bin/env python3
"""
立即修复API配置模型选择问题
"""

import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.db.base import SessionLocal
from backend.db.models import DBLLMConfig

def fix_model_selection():
    """修复模型选择问题"""
    
    print("=" * 80)
    print("🔧 立即修复API配置模型选择问题")
    print("=" * 80)
    
    db = SessionLocal()
    
    try:
        # 1. 查找当前用户ID
        print("\n[步骤1] 查找当前用户ID")
        print("-" * 50)
        
        # 查找有用户ID的配置
        user_configs = db.query(DBLLMConfig).filter(DBLLMConfig.user_id != None).all()
        
        if not user_configs:
            print("❌ 没有找到用户特定的配置")
            return False
            
        user_id = user_configs[0].user_id
        print(f"📋 找到用户ID: {user_id}")
        
        # 2. 禁用全局配置的激活状态
        print("\n[步骤2] 禁用全局配置的激活状态")
        print("-" * 50)
        
        global_count = db.query(DBLLMConfig).filter(
            DBLLMConfig.user_id == None,
            DBLLMConfig.is_active == True
        ).count()
        
        if global_count > 0:
            db.query(DBLLMConfig).filter(
                DBLLMConfig.user_id == None,
                DBLLMConfig.is_active == True
            ).update({DBLLMConfig.is_active: False})
            print(f"✅ 已禁用 {global_count} 个全局激活配置")
        else:
            print("ℹ️ 没有需要禁用的全局激活配置")
        
        # 3. 激活用户特定配置
        print("\n[步骤3] 激活用户特定配置")
        print("-" * 50)
        
        user_configs = db.query(DBLLMConfig).filter(
            DBLLMConfig.user_id == user_id
        ).all()
        
        print(f"📊 用户 {user_id} 共有 {len(user_configs)} 个配置:")
        
        for config in user_configs:
            print(f"  🔹 {config.name}: {config.default_model} (激活: {'✅' if config.is_active else '❌'})")
        
        # 查找gemini-3-pro-preview配置
        pro_config = db.query(DBLLMConfig).filter(
            DBLLMConfig.user_id == user_id,
            DBLLMConfig.default_model == 'gemini-3-pro-preview'
        ).first()
        
        if pro_config:
            pro_config.is_active = True
            print(f"✅ 已激活用户配置: {pro_config.name} - {pro_config.default_model}")
        else:
            print("❌ 没有找到gemini-3-pro-preview配置")
            
            # 如果没有找到，激活第一个用户配置
            if user_configs:
                user_configs[0].is_active = True
                print(f"✅ 已激活第一个用户配置: {user_configs[0].name} - {user_configs[0].default_model}")
        
        # 4. 提交更改
        db.commit()
        print("\n✅ 数据库更改已提交")
        
        # 5. 验证修复结果
        print("\n[步骤4] 验证修复结果")
        print("-" * 50)
        
        from backend.core.storage import get_active_llm_config, get_llm_active
        
        llm_cfg = get_active_llm_config(db, user_id)
        llm_active = get_llm_active(db, user_id)
        
        print(f"📋 修复后配置状态:")
        print(f"  配置ID: {llm_cfg.get('id') if llm_cfg else '无'}")
        print(f"  配置名称: {llm_cfg.get('name') if llm_cfg else '无'}")
        print(f"  默认模型: {llm_cfg.get('default_model') if llm_cfg else '无'}")
        print(f"  激活模型: {llm_active.get('model') if llm_active else '无'}")
        
        if llm_active.get('model') == 'gemini-3-pro-preview':
            print("🎉 修复成功！现在将使用 gemini-3-pro-preview 模型")
        else:
            print("⚠️ 修复后模型仍不是 gemini-3-pro-preview")
            print("  可能需要在前端重新选择模型")
        
        return True
        
    except Exception as e:
        print(f"❌ 修复过程中出现错误: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
        return False
    finally:
        db.close()

if __name__ == "__main__":
    fix_model_selection()