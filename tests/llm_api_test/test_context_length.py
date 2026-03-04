#!/usr/bin/env python3
"""
测试与原项目完全相同的消息长度
"""

import json
import time
import httpx
from pathlib import Path

CONFIG_PATH = Path(__file__).parent / "config.json"

def load_config():
    with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)

def normalize_base_url(base_url: str) -> str:
    s = (base_url or "").rstrip("/")
    if not s:
        return s
    import re
    if re.search(r"/v1$", s):
        return s
    return s + "/v1"

def test_with_long_context(api_config: dict, context_len: int):
    """测试指定长度的上下文消息"""
    print(f"\n{'='*70}")
    print(f"测试上下文长度: {context_len} 字符")
    print(f"{'='*70}")
    
    url = normalize_base_url(api_config['base_url']) + "/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_config['api_key']}",
        "Content-Type": "application/json",
    }
    
    # 构建指定长度的上下文
    base_context = """以下是当前故事运行时上下文：
【主角】
- id: CHAR_001  名称: 未知

【世界书（节选）】
- [ability_system] 灵气等级与境界划分: 云泽大陆的修炼者统称为'控灵者'。境界分为：
1. 纳灵境：感应天地灵气，开辟丹田。
2. 筑元境：灵气化液，铸就根基。
3. 破虚境：神识出窍，可短距离瞬移。
4. 登神阶：触碰法则，寿元达千载。
每个境界分为九重小境界，突破难度递增。
"""
    
    # 填充到目标长度
    filler = "\n- [条目] 这是一段测试填充内容，用于模拟世界书中的条目。"
    while len(base_context) < context_len:
        base_context += filler
    
    base_context = base_context[:context_len]
    
    messages = [
        {
            "role": "system",
            "content": """--- charPersonality ---
你是一个擅长中文叙事的互动小说引擎。你的任务是：
1. 根据用户的输入，生成连贯、有趣的剧情
2. 保持角色性格的一致性
3. 提供多样化的选择，让玩家有参与感"""
        },
        {
            "role": "system",
            "content": base_context
        },
        {
            "role": "user",
            "content": "【追踪小径】对方很可能逃入了迷雾森林，沿小径追踪。"
        }
    ]
    
    payload = {
        "model": api_config['model'],
        "messages": messages,
        "temperature": 0.8,
        "stream": True,
    }
    
    payload_size = len(json.dumps(payload, ensure_ascii=False))
    print(f"Payload JSON size: {payload_size} bytes")
    print(f"message[1] length: {len(base_context)} chars")
    
    content_received = ""
    line_count = 0
    first_lines = []
    
    try:
        start = time.time()
        with httpx.Client(timeout=120.0) as client:
            with client.stream("POST", url, headers=headers, json=payload) as r:
                print(f"HTTP状态码: {r.status_code}")
                
                if r.status_code >= 400:
                    text = r.read().decode("utf-8", errors="ignore")
                    print(f"错误响应: {text[:500]}")
                    return False, payload_size
                
                for line in r.iter_lines():
                    line_count += 1
                    if line_count <= 3:
                        first_lines.append(line[:200])
                    
                    if not line:
                        continue
                    if line.startswith("data:"):
                        chunk = line[len("data:"):].strip()
                    else:
                        chunk = line.strip()
                    
                    if chunk == "[DONE]":
                        break
                    
                    try:
                        obj = json.loads(chunk)
                        choices = obj.get("choices", [])
                        if choices:
                            delta = choices[0].get("delta") or {}
                            content = delta.get("content")
                            if content:
                                content_received += content
                            finish_reason = choices[0].get("finish_reason")
                            if finish_reason and line_count <= 3:
                                print(f"Line {line_count}: finish_reason={finish_reason}")
                    except:
                        pass
                
                elapsed = time.time() - start
                success = len(content_received) > 0
                
                print(f"结果: 行数={line_count}, 内容长度={len(content_received)}, 耗时={elapsed:.1f}s")
                
                if not success:
                    print("前3行原始数据:")
                    for i, line in enumerate(first_lines, 1):
                        print(f"  {i}: {line}")
                
                return success, payload_size
                    
    except Exception as e:
        print(f"错误: {e}")
        return False, payload_size

def main():
    config = load_config()
    
    for api_config in config['apis']:
        if api_config['name'] == 'GG公益站':
            # 测试不同长度，找出临界点
            # 原项目是 6541 bytes，message[1] 是 5576 chars
            test_cases = [
                (1000, "1KB"),
                (3000, "3KB"),
                (5000, "5KB"),
                (5500, "5.5KB (接近原项目)"),
                (6000, "6KB"),
            ]
            
            results = []
            
            for context_len, desc in test_cases:
                print(f"\n>>> 测试 {desc}")
                success, payload_size = test_with_long_context(api_config, context_len)
                results.append((desc, context_len, payload_size, success))
                time.sleep(1)
            
            print(f"\n{'='*70}")
            print("测试汇总:")
            print(f"{'描述':<20} {'上下文长度':<12} {'Payload大小':<12} {'结果'}")
            print("-" * 60)
            for desc, ctx_len, payload_size, success in results:
                status = "✅ 成功" if success else "❌ 失败"
                print(f"{desc:<20} {ctx_len:<12} {payload_size:<12} {status}")
            
            # 找临界点
            failed = [(d, c, p) for d, c, p, s in results if not s]
            if failed:
                print(f"\n⚠️ 超过某个阈值后API返回空响应")

if __name__ == '__main__':
    main()
