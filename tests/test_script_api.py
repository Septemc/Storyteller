#!/usr/bin/env python3
"""
[测试脚本] 验证 Script 持久化 API

功能：
1. 创建/更新脚本
2. 创建/更新副本
3. 更新会话状态绑定脚本
4. 查询脚本和会话数据

用法：
  python tests/test_script_api.py
"""

import sys
import json
import requests
from pathlib import Path

# API 基地址
BASE_URL = "http://localhost:8010/api"
SESSION_ID = "test_session_001"

def log_section(title):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")

def test_create_script():
    """测试：创建脚本"""
    log_section("1️⃣  创建脚本")
    
    payload = {
        "script_id": "test_script_001",
        "name": "测试剧本：魔王城堡",
        "description": "一个关于勇者进攻魔王城堡的故事",
        "dungeon_ids": [],  # 先创建空脚本，之后再添加副本
        "meta": {"category": "fantasy"}
    }
    
    resp = requests.put(f"{BASE_URL}/scripts/test_script_001", json=payload)
    if resp.status_code == 200:
        print(f"✅ 脚本创建成功:")
        print(json.dumps(resp.json(), indent=2, ensure_ascii=False))
        return resp.json()
    else:
        print(f"❌ 失败 ({resp.status_code}): {resp.text}")
        return None

def test_create_dungeon():
    """测试：创建副本"""
    log_section("2️⃣  创建副本")
    
    payload = {
        "dungeon_id": "dun_test_001",
        "name": "第一关：城堡入口",
        "description": "魔王城堡的第一道防线",
        "level_min": 5,
        "level_max": 10,
        "global_rules": {"difficulty": "hard"},
        "nodes": [
            {
                "node_id": "node_001",
                "name": "开场：城门前",
                "index": 0,
                "progress_percent": 0,
                "entry_conditions": [],
                "exit_conditions": [{"type": "defeat_guards"}],
                "summary_requirements": "击败守卫",
                "story_requirements": {},
                "branching": {}
            },
            {
                "node_id": "node_002",
                "name": "进展：通过走廊",
                "index": 1,
                "progress_percent": 50,
                "entry_conditions": [{"required_node": "node_001"}],
                "exit_conditions": [{"type": "reach_stairs"}],
                "summary_requirements": "找到通往上层的楼梯",
                "story_requirements": {},
                "branching": {}
            }
        ]
    }
    
    resp = requests.put(f"{BASE_URL}/dungeon/dun_test_001", json=payload)
    if resp.status_code == 200:
        print(f"✅ 副本创建成功:")
        print(json.dumps(resp.json(), indent=2, ensure_ascii=False))
        return resp.json()
    else:
        print(f"❌ 失败 ({resp.status_code}): {resp.text}")
        return None

def test_update_script_with_dungeon():
    """测试：更新脚本，关联副本"""
    log_section("3️⃣  更新脚本，添加副本关联")
    
    payload = {
        "script_id": "test_script_001",
        "name": "测试剧本：魔王城堡 [已关联副本]",
        "description": "一个关于勇者进攻魔王城堡的故事",
        "dungeon_ids": ["dun_test_001"],  # 关联刚才创建的副本
        "meta": {"category": "fantasy", "difficulty": "hard"}
    }
    
    resp = requests.put(f"{BASE_URL}/scripts/test_script_001", json=payload)
    if resp.status_code == 200:
        print(f"✅ 脚本更新成功:")
        print(json.dumps(resp.json(), indent=2, ensure_ascii=False))
        return resp.json()
    else:
        print(f"❌ 失败 ({resp.status_code}): {resp.text}")
        return None

def test_get_scripts():
    """测试：获取脚本列表"""
    log_section("4️⃣  获取脚本列表")
    
    resp = requests.get(f"{BASE_URL}/scripts")
    if resp.status_code == 200:
        data = resp.json()
        print(f"✅ 获取成功，共 {len(data['items'])} 个脚本:")
        for item in data['items']:
            print(f"  - {item['script_id']}: {item['name']}")
        return data
    else:
        print(f"❌ 失败 ({resp.status_code}): {resp.text}")
        return None

def test_get_script_detail():
    """测试：获取脚本详情"""
    log_section("5️⃣  获取脚本详情")
    
    resp = requests.get(f"{BASE_URL}/scripts/test_script_001")
    if resp.status_code == 200:
        data = resp.json()
        print(f"✅ 获取成功:")
        print(json.dumps(data, indent=2, ensure_ascii=False))
        return data
    else:
        print(f"❌ 失败 ({resp.status_code}): {resp.text}")
        return None

def test_update_session_context():
    """测试：更新会话，绑定脚本和副本"""
    log_section("6️⃣  更新会话上下文（绑定脚本/副本/节点）")
    
    payload = {
        "session_id": SESSION_ID,
        "current_script_id": "test_script_001",
        "current_dungeon_id": "dun_test_001",
        "current_node_id": "node_001"
    }
    
    resp = requests.post(f"{BASE_URL}/session/context", json=payload)
    if resp.status_code == 200:
        data = resp.json()
        print(f"✅ 会话更新成功:")
        print(json.dumps(data, indent=2, ensure_ascii=False))
        return data
    else:
        print(f"❌ 失败 ({resp.status_code}): {resp.text}")
        return None

def test_get_session_summary():
    """测试：获取会话摘要"""
    log_section("7️⃣  获取会话摘要")
    
    resp = requests.get(f"{BASE_URL}/session/summary?session_id={SESSION_ID}")
    if resp.status_code == 200:
        data = resp.json()
        print(f"✅ 取得成功:")
        print(json.dumps(data, indent=2, ensure_ascii=False))
        return data
    else:
        print(f"❌ 失败 ({resp.status_code}): {resp.text}")
        return None

def test_get_dungeon():
    """测试：获取副本详情"""
    log_section("8️⃣  获取副本详情")
    
    resp = requests.get(f"{BASE_URL}/dungeon/dun_test_001")
    if resp.status_code == 200:
        data = resp.json()
        print(f"✅ 取得成功:")
        print(f"  副本ID: {data['dungeon_id']}")
        print(f"  名称: {data['name']}")
        print(f"  节点数: {len(data['nodes'])}")
        for node in data['nodes']:
            print(f"    - {node['node_id']}: {node['name']}")
        return data
    else:
        print(f"❌ 失败 ({resp.status_code}): {resp.text}")
        return None

def verify_database():
    """验证：直接查询数据库"""
    log_section("9️⃣  验证数据库中的数据")
    
    try:
        import sqlite3
        conn = sqlite3.connect('data/db.sqlite')
        c = conn.cursor()
        
        # 查询脚本
        print("\n📊 scripts 表:")
        c.execute('SELECT script_id, name, dungeon_ids_json FROM scripts ORDER BY script_id')
        for row in c.fetchall():
            print(f"  - {row[0]}: {row[1]}")
            print(f"    关联副本: {row[2]}")
        
        # 查询会话
        print("\n📊 session_state 表当前会话:")
        c.execute(f'SELECT session_id, current_script_id, current_dungeon_id, current_node_id FROM session_state WHERE session_id = ?', (SESSION_ID,))
        row = c.fetchone()
        if row:
            print(f"  会话ID: {row[0]}")
            print(f"  脚本: {row[1]}")
            print(f"  副本: {row[2]}")
            print(f"  节点: {row[3]}")
        
        # 查询副本
        print("\n📊 dungeons 表:")
        c.execute('SELECT dungeon_id, name FROM dungeons ORDER BY dungeon_id')
        for row in c.fetchall():
            print(f"  - {row[0]}: {row[1]}")
        
        conn.close()
        print("\n✅ 数据库验证完成")
        
    except Exception as e:
        print(f"❌ 数据库查询失败: {e}")

def main():
    """主测试流程"""
    print("\n" + "="*60)
    print("  🧪 Script 持久化 API 测试")
    print("="*60)
    print(f"API 基地址: {BASE_URL}")
    print(f"测试会话ID: {SESSION_ID}")
    
    try:
        # 1. 创建脚本
        test_create_script()
        
        # 2. 创建副本
        test_create_dungeon()
        
        # 3. 更新脚本关联副本
        test_update_script_with_dungeon()
        
        # 4. 获取脚本列表
        test_get_scripts()
        
        # 5. 获取脚本详情
        test_get_script_detail()
        
        # 6. 更新会话
        test_update_session_context()
        
        # 7. 获取会话摘要
        test_get_session_summary()
        
        # 8. 获取副本详情
        test_get_dungeon()
        
        # 9. 验证数据库
        verify_database()
        
        print("\n" + "="*60)
        print("  ✅ 所有测试完成！")
        print("="*60)
        
    except requests.exceptions.ConnectionError:
        print("\n❌ 无法连接到 API 服务器！")
        print("请确保已启动后端服务: uvicorn backend.main:app --reload --port 8010")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 测试出错: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
