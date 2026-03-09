#!/usr/bin/env python3
"""
设置默认模型为gemini-3-flash-preview
同时保持激活模型选择功能
"""

import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.db.base import SessionLocal
from backend.db.models import DBLLMConfig

def set_default_model():
    """设置默认模型为gemini-3-flash-preview"""
    
    print("=" * 80)
    print("🔧 设置默认模型为gemini-3-flash-preview")
    print("=" * 80)
    
    db = SessionLocal()
    
    try:
        # 1. 查找所有配置
        print("\n[步骤1] 检查当前所有配置")
        print("-" * 50)
        
        all_configs = db.query(DBLLMConfig).all()
        print(f"📊 数据库中共有 {len(all_configs)} 个LLM配置:")
        
        for i, config in enumerate(all_configs):
            print(f"\n  🔹 配置 #{i+1}:")
            print(f"    配置ID: {config.id}")
            print(f"    配置名称: {config.name}")
            print(f"    是否激活: {'✅ 是' if config.is_active else '❌ 否'}")
            print(f"    默认模型: {config.default_model}")
            print(f"    Base URL: {config.base_url}")
            print(f"    用户ID: {config.user_id}")
        
        # 2. 设置默认模型
        print("\n[步骤2] 设置默认模型为gemini-3-flash-preview")
        print("-" * 50)
        
        # 查找GG公益站配置
        gg_configs = db.query(DBLLMConfig).filter(
            DBLLMConfig.name.like('%GG公益站%')
        ).all()
        
        if not gg_configs:
            print("❌ 没有找到GG公益站配置")
            return False
        
        # 设置所有GG公益站配置的默认模型为gemini-3-flash-preview
        updated_count = 0
        for config in gg_configs:
            if config.default_model != 'gemini-3-flash-preview':
                old_model = config.default_model
                config.default_model = 'gemini-3-flash-preview'
                updated_count += 1
                print(f"✅ 更新配置 {config.name}: {old_model} → gemini-3-flash-preview")
            else:
                print(f"ℹ️ 配置 {config.name} 已经是 gemini-3-flash-preview")
        
        # 3. 设置激活状态
        print("\n[步骤3] 设置激活状态")
        print("-" * 50)
        
        # 禁用所有激活状态
        db.query(DBLLMConfig).filter(DBLLMConfig.is_active == True).update({DBLLMConfig.is_active: False})
        print("✅ 已禁用所有激活配置")
        
        # 激活用户特定的配置（如果存在）
        user_configs = db.query(DBLLMConfig).filter(DBLLMConfig.user_id != None).all()
        
        if user_configs:
            # 激活第一个用户特定配置
            user_config = user_configs[0]
            user_config.is_active = True
            print(f"✅ 已激活用户配置: {user_config.name} - {user_config.default_model}")
        else:
            # 如果没有用户配置，激活第一个全局配置
            global_config = db.query(DBLLMConfig).filter(DBLLMConfig.user_id == None).first()
            if global_config:
                global_config.is_active = True
                print(f"✅ 已激活全局配置: {global_config.name} - {global_config.default_model}")
        
        # 4. 提交更改
        db.commit()
        print("\n✅ 数据库更改已提交")
        
        # 5. 验证设置结果
        print("\n[步骤4] 验证设置结果")
        print("-" * 50)
        
        from backend.core.storage import get_active_llm_config, get_llm_active
        
        # 检查用户特定配置
        user_id = user_configs[0].user_id if user_configs else None
        llm_cfg = get_active_llm_config(db, user_id)
        llm_active = get_llm_active(db, user_id)
        
        print(f"📋 设置后配置状态:")
        print(f"  配置ID: {llm_cfg.get('id') if llm_cfg else '无'}")
        print(f"  配置名称: {llm_cfg.get('name') if llm_cfg else '无'}")
        print(f"  默认模型: {llm_cfg.get('default_model') if llm_cfg else '无'}")
        print(f"  激活模型: {llm_active.get('model') if llm_active else '无'}")
        
        # 检查所有GG公益站配置的默认模型
        gg_configs_after = db.query(DBLLMConfig).filter(
            DBLLMConfig.name.like('%GG公益站%')
        ).all()
        
        print(f"\n📊 GG公益站配置默认模型检查:")
        all_correct = True
        for config in gg_configs_after:
            status = "✅" if config.default_model == 'gemini-3-flash-preview' else "❌"
            print(f"  {status} {config.name}: {config.default_model}")
            if config.default_model != 'gemini-3-flash-preview':
                all_correct = False
        
        if all_correct:
            print("\n🎉 所有GG公益站配置的默认模型已设置为 gemini-3-flash-preview")
        else:
            print("\n⚠️ 部分配置的默认模型设置失败")
        
        print("\n💡 使用说明:")
        print("  - 默认模型: gemini-3-flash-preview (所有新配置的默认值)")
        print("  - 激活模型: 可以在前端设置页面选择其他模型")
        print("  - 系统将优先使用激活模型，如果没有激活模型则使用默认模型")
        
        return True
        
    except Exception as e:
        print(f"❌ 设置过程中出现错误: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
        return False
    finally:
        db.close()

if __name__ == "__main__":
    set_default_model()