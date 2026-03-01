"""
测试存档管理API功能
"""
import sys
import json
import urllib.request
import urllib.error
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

BASE_URL = "http://127.0.0.1:8000/api"


def fetch(url, params=None):
    if params:
        query = "&".join(f"{k}={v}" for k, v in params.items())
        url = f"{url}?{query}"
    
    try:
        with urllib.request.urlopen(url) as response:
            return response.status, json.loads(response.read().decode('utf-8'))
    except urllib.error.HTTPError as e:
        return e.code, {"error": e.read().decode('utf-8')}
    except Exception as e:
        return None, {"error": str(e)}


def test_saves_list():
    print("\n" + "=" * 50)
    print("测试: 获取存档列表")
    print("=" * 50)
    
    status, data = fetch(f"{BASE_URL}/story/saves/list")
    print(f"状态码: {status}")
    
    if status == 200:
        saves = data
        print(f"存档数量: {len(saves)}")
        for save in saves[:3]:
            print(f"  - {save.get('display_name', 'N/A')} ({save.get('session_id', 'N/A')})")
        return saves[0]['session_id'] if saves else None
    else:
        print(f"错误: {data}")
        return None


def test_save_detail(session_id):
    print("\n" + "=" * 50)
    print(f"测试: 获取存档详情 (session_id={session_id})")
    print("=" * 50)
    
    status, detail = fetch(f"{BASE_URL}/story/saves/detail", {"session_id": session_id})
    print(f"状态码: {status}")
    
    if status == 200:
        print(f"存档名称: {detail.get('display_name', 'N/A')}")
        print(f"分段数量: {detail.get('segment_count', 0)}")
        print(f"总字数: {detail.get('total_word_count', 0)}")
        
        segments = detail.get('segments', [])
        print(f"\n分段列表 (前5条):")
        for seg in segments[:5]:
            preview = seg.get('preview', '(无预览)')[:50]
            print(f"  #{seg.get('index', 0)}: {preview}... ({seg.get('word_count', 0)}字)")
        
        return True
    else:
        print(f"错误: {detail}")
        return False


def main():
    print("=" * 50)
    print("存档管理API测试")
    print("=" * 50)
    
    session_id = test_saves_list()
    
    if session_id:
        test_save_detail(session_id)
    else:
        print("\n没有找到存档，跳过详情测试")
    
    print("\n" + "=" * 50)
    print("测试完成")
    print("=" * 50)


if __name__ == "__main__":
    main()
