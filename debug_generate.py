"""
详细调试生成功能的问题

使用方式：
python debug_generate.py
"""

import requests
import json
import time
import traceback

def debug_generate_function():
    """详细调试生成功能"""
    
    base_url = "http://127.0.0.1:8010"
    
    # 测试数据
    test_data = {
        "session_id": "debug_session_" + str(int(time.time())),
        "user_input": "主角走进森林，发现一个神秘的洞穴",
        "frontend_duration": 0.0
    }
    
    print("=" * 60)
    print("详细调试生成功能")
    print("=" * 60)
    
    try:
        # 测试1：检查服务器是否运行
        print("\n[步骤1] 检查服务器状态...")
        response = requests.get(f"{base_url}/docs", timeout=10)
        if response.status_code == 200:
            print("  ✅ 服务器运行正常")
        else:
            print(f"  ❌ 服务器异常，状态码: {response.status_code}")
            return False
        
        # 测试2：检查API文档是否可访问
        print("\n[步骤2] 检查API文档...")
        response = requests.get(f"{base_url}/openapi.json", timeout=10)
        if response.status_code == 200:
            openapi_data = response.json()
            paths = openapi_data.get('paths', {})
            if '/api/story/generate' in paths:
                print("  ✅ 生成API路由存在")
            else:
                print("  ❌ 生成API路由不存在")
                return False
        else:
            print(f"  ❌ 无法获取API文档，状态码: {response.status_code}")
            return False
        
        # 测试3：详细测试生成路由
        print("\n[步骤3] 详细测试生成路由...")
        print(f"  请求数据: {json.dumps(test_data, ensure_ascii=False, indent=2)}")
        
        start_time = time.time()
        
        try:
            response = requests.post(
                f"{base_url}/api/story/generate",
                json=test_data,
                headers={"Content-Type": "application/json"},
                timeout=120
            )
            
            end_time = time.time()
            duration = end_time - start_time
            
            print(f"  请求耗时: {duration:.2f}秒")
            print(f"  状态码: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                print("  ✅ 生成路由请求成功")
                print(f"  生成内容长度: {len(result.get('story', ''))} 字符")
                print(f"  元数据: {json.dumps(result.get('meta', {}), ensure_ascii=False, indent=2)}")
                
                # 显示部分生成内容
                story_text = result.get('story', '')
                if story_text:
                    print(f"  生成内容预览: {story_text[:300]}...")
                
                return True
                
            elif response.status_code == 422:
                print("  ❌ 请求数据格式错误")
                error_details = response.json()
                print(f"  错误详情: {json.dumps(error_details, ensure_ascii=False, indent=2)}")
                
            elif response.status_code == 500:
                print("  ❌ 服务器内部错误")
                print("  错误响应内容:")
                print(f"  {response.text}")
                
                # 尝试解析错误详情
                try:
                    error_data = response.json()
                    print("  解析的错误详情:")
                    print(f"  {json.dumps(error_data, ensure_ascii=False, indent=2)}")
                except:
                    print("  无法解析JSON错误响应")
                
            else:
                print(f"  ❌ 未知错误: {response.status_code}")
                print(f"  响应内容: {response.text}")
                
        except requests.exceptions.Timeout:
            print("  ❌ 请求超时，AI服务可能无法访问或处理时间过长")
            print("  请检查AI服务配置和网络连接")
            
        except Exception as e:
            print(f"  ❌ 请求过程中出现异常: {e}")
            print("  异常详情:")
            traceback.print_exc()
            
    except requests.exceptions.ConnectionError:
        print("  ❌ 无法连接到服务器，请检查服务器是否运行")
        print("  运行命令: python -m uvicorn backend.main:app --reload --port 8010")
        
    except Exception as e:
        print(f"  ❌ 调试过程中出现异常: {e}")
        traceback.print_exc()
    
    return False

def check_ai_service_config():
    """检查AI服务配置"""
    
    print("\n[步骤4] 检查AI服务配置...")
    
    try:
        # 直接查询数据库配置
        import sys
        from pathlib import Path
        sys.path.insert(0, str(Path(__file__).parent))
        
        from backend.db.base import SessionLocal
        from backend.core.storage import get_active_llm_config, get_llm_active
        
        db = SessionLocal()
        
        llm_cfg = get_active_llm_config(db)
        llm_active = get_llm_active(db)
        
        print("  当前LLM配置:")
        print(f"    - 服务名称: {llm_cfg.get('name', '未知')}")
        print(f"    - 服务地址: {llm_cfg.get('base_url', '未知')}")
        print(f"    - 模型: {llm_active.get('model', '未知')}")
        print(f"    - API密钥状态: {'已配置' if llm_cfg.get('api_key') else '未配置'}")
        
        # 测试AI服务连接
        test_url = f"{llm_cfg.get('base_url')}/v1/models"
        print(f"  测试连接: {test_url}")
        
        response = requests.get(test_url, timeout=10)
        
        if response.status_code == 200:
            print("  ✅ AI服务端点可访问")
            return True
        else:
            print(f"  ❌ AI服务端点异常，状态码: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"  ❌ 检查AI服务配置失败: {e}")
        traceback.print_exc()
        return False

def main():
    """主调试函数"""
    
    print("Storyteller 生成功能详细调试工具")
    print("=" * 60)
    
    # 检查AI服务配置
    ai_ok = check_ai_service_config()
    
    # 调试生成功能
    if ai_ok:
        generate_ok = debug_generate_function()
        
        if generate_ok:
            print("\n🎉 生成功能调试通过！")
            print("  前端可以正常使用'生成下一段'功能")
        else:
            print("\n⚠️  生成功能存在问题")
            print("  请查看服务器日志获取详细错误信息")
    else:
        print("\n❌ AI服务配置或连接有问题")
        print("  请检查AI服务配置")
    
    print("\n" + "=" * 60)
    print("调试完成")

if __name__ == "__main__":
    main()