"""
直接测试生成功能的路由测试脚本

使用方式：
python test_generate_route.py
"""

import requests
import json
import time

def test_generate_route():
    """测试生成路由的完整功能"""
    
    base_url = "http://127.0.0.1:8010"
    
    # 测试数据
    test_data = {
        "session_id": "test_session_" + str(int(time.time())),
        "user_input": "主角走进森林，发现一个神秘的洞穴",
        "frontend_duration": 0.0
    }
    
    print("=" * 60)
    print("开始测试生成路由功能")
    print("=" * 60)
    
    try:
        # 测试1：检查服务器是否运行
        print("\n[测试1] 检查服务器状态...")
        response = requests.get(f"{base_url}/docs", timeout=10)
        if response.status_code == 200:
            print("  ✅ 服务器运行正常")
        else:
            print(f"  ❌ 服务器异常，状态码: {response.status_code}")
            return False
        
        # 测试2：测试生成路由
        print("\n[测试2] 测试生成路由 /story/generate...")
        start_time = time.time()
        
        response = requests.post(
            f"{base_url}/api/story/generate",
            json=test_data,
            headers={"Content-Type": "application/json"},
            timeout=120  # 2分钟超时
        )
        
        end_time = time.time()
        duration = end_time - start_time
        
        print(f"  请求耗时: {duration:.2f}秒")
        print(f"  状态码: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("  ✅ 生成路由请求成功")
            print(f"  生成内容长度: {len(result.get('story', ''))} 字符")
            print(f"  元数据: {result.get('meta', {})}")
            
            # 显示部分生成内容
            story_text = result.get('story', '')
            if story_text:
                print(f"  生成内容预览: {story_text[:200]}...")
            
            return True
            
        elif response.status_code == 422:
            print("  ❌ 请求数据格式错误")
            print(f"  错误详情: {response.text}")
            
        elif response.status_code == 500:
            print("  ❌ 服务器内部错误")
            print(f"  错误详情: {response.text}")
            
        else:
            print(f"  ❌ 未知错误: {response.status_code}")
            print(f"  响应内容: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("  ❌ 无法连接到服务器，请检查服务器是否运行")
        print("  运行命令: python -m uvicorn backend.main:app --reload --port 8010")
        
    except requests.exceptions.Timeout:
        print("  ❌ 请求超时，AI服务可能无法访问")
        print("  请检查网络连接和AI服务配置")
        
    except Exception as e:
        print(f"  ❌ 测试过程中出现异常: {e}")
    
    return False

def test_ai_service_connection():
    """测试AI服务连接性"""
    
    print("\n[测试3] 测试AI服务连接性...")
    
    try:
        # 直接测试AI服务端点
        test_url = "https://gcli.ggchan.dev/v1/models"
        
        response = requests.get(test_url, timeout=10)
        
        if response.status_code == 200:
            print("  ✅ AI服务端点可访问")
            return True
        else:
            print(f"  ❌ AI服务端点异常，状态码: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"  ❌ AI服务连接失败: {e}")
        return False

def main():
    """主测试函数"""
    
    print("Storyteller 生成功能测试工具")
    print("=" * 60)
    
    # 测试AI服务连接
    ai_connected = test_ai_service_connection()
    
    # 测试生成路由
    if ai_connected:
        route_working = test_generate_route()
        
        if route_working:
            print("\n🎉 生成功能测试通过！")
            print("  前端可以正常使用'生成下一段'功能")
        else:
            print("\n⚠️  生成功能存在问题")
            print("  请检查服务器日志获取详细错误信息")
    else:
        print("\n❌ AI服务无法连接")
        print("  请检查网络连接或更换AI服务配置")
    
    print("\n" + "=" * 60)

if __name__ == "__main__":
    main()