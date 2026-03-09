#!/usr/bin/env python3
"""
诊断API配置模型选择问题
检查为什么选择了gemini-3-pro-preview但实际使用gemini-3-flash-preview
"""

import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.db.base import SessionLocal
from backend.core.storage import get_active_llm_config, get_llm_active

def diagnose_model_selection():
    """诊断模型选择问题"""
    
    print("=" * 80)
    print("🔍 API配置模型选择问题诊断")
    print("=" * 80)
    
    db = SessionLocal()
    
    try:
        # 1. 获取当前激活的LLM配置
        print("\n[步骤1] 检查当前激活的LLM配置")
        print("-" * 50)
        
        llm_cfg = get_active_llm_config(db)
        llm_active = get_llm_active(db)
        
        print(f"📋 LLM配置详情:")
        print(f"  配置ID: {llm_cfg.get('id') if llm_cfg else '无'}")
        print(f"  配置名称: {llm_cfg.get('name') if llm_cfg else '无'}")
        print(f"  Base URL: {llm_cfg.get('base_url') if llm_cfg else '无'}")
        print(f"  API密钥状态: {'已配置' if llm_cfg and llm_cfg.get('api_key') else '未配置'}")
        print(f"  默认模型: {llm_cfg.get('default_model') if llm_cfg else '无'}")
        print(f"  流式模式: {llm_cfg.get('stream') if llm_cfg else '无'}")
        
        print(f"\n📊 激活状态:")
        print(f"  激活配置ID: {llm_active.get('config_id') if llm_active else '无'}")
        print(f"  激活模型: {llm_active.get('model') if llm_active else '无'}")
        
        # 2. 检查数据库中的实际配置
        print("\n[步骤2] 检查数据库中的实际配置")
        print("-" * 50)
        
        from backend.db.models import DBLLMConfig
        
        # 获取所有配置
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
        
        # 3. 分析问题
        print("\n[步骤3] 问题分析")
        print("-" * 50)
        
        if not llm_cfg:
            print("❌ 问题: 没有找到激活的LLM配置")
            return False
        
        # 检查模型选择逻辑
        expected_model = "gemini-3-pro-preview"
        actual_model = llm_active.get('model') or llm_cfg.get('default_model')
        
        print(f"🔍 模型选择分析:")
        print(f"  期望模型: {expected_model}")
        print(f"  实际模型: {actual_model}")
        print(f"  激活模型: {llm_active.get('model')}")
        print(f"  默认模型: {llm_cfg.get('default_model')}")
        
        if actual_model == expected_model:
            print("✅ 模型选择正确")
        else:
            print("❌ 模型选择不一致")
            
            if llm_active.get('model') != expected_model:
                print("  🔸 问题: 激活模型与期望不一致")
                print("    可能原因: 前端设置激活配置时没有正确传递模型参数")
                
            if llm_cfg.get('default_model') != expected_model:
                print("  🔸 问题: 默认模型与期望不一致")
                print("    可能原因: 配置保存时没有正确设置默认模型")
        
        # 4. 检查前端设置逻辑
        print("\n[步骤4] 检查前端设置逻辑")
        print("-" * 50)
        
        # 检查前端设置API的调用
        print("🔍 前端设置流程分析:")
        print("  1. 用户选择模型")
        print("  2. 前端调用 /api/llm/active 接口")
        print("  3. 后端更新 DBLLMConfig.is_active 和 default_model")
        print("  4. 生成时使用 llm_active.get('model') 或 llm_cfg.get('default_model')")
        
        # 5. 建议修复方案
        print("\n[步骤5] 修复建议")
        print("-" * 50)
        
        print("🔧 可能的修复方案:")
        print("  1. 检查前端设置激活配置时是否传递了正确的 model 参数")
        print("  2. 检查 /api/llm/active 接口是否正确处理 model 参数")
        print("  3. 检查数据库中的 default_model 字段是否正确保存")
        print("  4. 在 orchestrator.py 中添加更详细的调试日志")
        
        return True
        
    except Exception as e:
        print(f"❌ 诊断过程中出现错误: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()

if __name__ == "__main__":
    diagnose_model_selection()