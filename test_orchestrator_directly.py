"""
直接测试orchestrator模块，定位生成功能的具体问题

使用方式：
python test_orchestrator_directly.py
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from backend.db.base import SessionLocal
from backend.core.orchestrator import generate_story_text
import traceback

def test_orchestrator_directly():
    """直接测试orchestrator模块"""
    
    print("=" * 60)
    print("直接测试orchestrator模块")
    print("=" * 60)
    
    db = SessionLocal()
    
    try:
        # 测试数据
        session_id = "direct_test_session_" + str(hash("test"))
        user_input = "主角走进森林，发现一个神秘的洞穴"
        
        print(f"\n[测试1] 测试orchestrator.generate_story_text...")
        print(f"  会话ID: {session_id}")
        print(f"  用户输入: {user_input}")
        
        # 直接调用orchestrator
        result = generate_story_text(
            db=db,
            session_id=session_id,
            user_input=user_input,
            force_stream=False
        )
        
        full_text, meta, stream_gen, dev_log_info = result
        
        print("  ✅ orchestrator调用成功")
        print(f"  生成内容长度: {len(full_text)} 字符")
        print(f"  元数据: {meta}")
        print(f"  流式生成器: {'存在' if stream_gen else '不存在'}")
        
        # 显示生成内容
        if full_text:
            print(f"  生成内容预览: {full_text[:300]}...")
        
        return True
        
    except Exception as e:
        print(f"  ❌ orchestrator调用失败: {e}")
        print("  异常详情:")
        traceback.print_exc()
        return False
    finally:
        db.close()

def test_llm_client():
    """测试LLM客户端连接"""
    
    print(f"\n[测试2] 测试LLM客户端连接...")
    
    try:
        from backend.core.storage import get_active_llm_config, get_llm_active
        from backend.core.llm_client import list_models
        
        db = SessionLocal()
        
        # 获取配置
        llm_cfg = get_active_llm_config(db)
        llm_active = get_llm_active(db)
        
        print(f"  LLM配置: {llm_cfg}")
        print(f"  激活模型: {llm_active}")
        
        # 测试模型列表
        base_url = llm_cfg.get('base_url')
        api_key = llm_cfg.get('api_key')
        
        if base_url and api_key:
            print(f"  测试连接: {base_url}")
            models = list_models(base_url, api_key)
            print(f"  ✅ 可用的模型: {models}")
            return True
        else:
            print("  ❌ 缺少base_url或api_key")
            return False
            
    except Exception as e:
        print(f"  ❌ LLM客户端测试失败: {e}")
        traceback.print_exc()
        return False

def main():
    """主测试函数"""
    
    print("Storyteller orchestrator模块直接测试")
    print("=" * 60)
    
    # 测试LLM客户端
    llm_ok = test_llm_client()
    
    # 测试orchestrator
    if llm_ok:
        orchestrator_ok = test_orchestrator_directly()
        
        if orchestrator_ok:
            print("\n🎉 orchestrator模块测试通过！")
            print("  问题可能出现在API路由层")
        else:
            print("\n⚠️  orchestrator模块存在问题")
            print("  问题出现在orchestrator层")
    else:
        print("\n❌ LLM客户端配置或连接有问题")
        print("  请检查AI服务配置")
    
    print("\n" + "=" * 60)
    print("测试完成")

if __name__ == "__main__":
    main()