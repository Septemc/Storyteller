#!/usr/bin/env python3
"""
测试消息长度对API的影响
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

def test_message_length(api_config: dict, msg_len: int):
    """测试不同消息长度"""
    print(f"\n{'='*70}")
    print(f"测试消息长度: {msg_len} 字符")
    print(f"{'='*70}")
    
    url = normalize_base_url(api_config['base_url']) + "/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_config['api_key']}",
        "Content-Type": "application/json",
    }
    
    # 生成指定长度的上下文消息
    long_context = "以下是当前故事运行时上下文：\n"
    long_context += "【世界书】\n"
    
    # 填充内容到目标长度
    filler = "这是一段测试内容，用于填充消息长度。"
    while len(long_context) < msg_len:
        long_context += f"- 条目{len(long_context)//20}: {filler}\n"
    
    long_context = long_context[:msg_len]  # 截断到目标长度
    
    messages = [
        {
            "role": "system",
            "content": "你是一个互动小说引擎，根据用户输入生成剧情。"
        },
        {
            "role": "system", 
            "content": long_context
        },
        {
            "role": "user",
            "content": "【追踪小径】沿小径追踪。"
        }
    ]
    
    payload = {
        "model": api_config['model'],
        "messages": messages,
        "temperature": 0.8,
        "stream": True,
    }
    
    total_chars = sum(len(m['content']) for m in messages)
    print(f"实际消息总长度: {total_chars}")
    
    content_received = ""
    line_count = 0
    
    try:
        start = time.time()
        with httpx.Client(timeout=120.0) as client:
            with client.stream("POST", url, headers=headers, json=payload) as r:
                print(f"HTTP状态码: {r.status_code}")
                
                if r.status_code >= 400:
                    text = r.read().decode("utf-8", errors="ignore")
                    print(f"错误响应: {text[:500]}")
                    return False
                
                for line in r.iter_lines():
                    line_count += 1
                    if line_count <= 3:
                        print(f"Line {line_count}: {line[:200]}")
                    
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
                            if finish_reason and line_count <= 5:
                                print(f"  Finish reason: {finish_reason}")
                    except:
                        pass
                
                elapsed = time.time() - start
                print(f"\n结果: 行数={line_count}, 内容长度={len(content_received)}, 耗时={elapsed:.1f}s")
                
                if content_received:
                    print(f"内容预览: {content_received[:100]}")
                    return True
                else:
                    print("⚠️ 没有收到内容!")
                    return False
                    
    except Exception as e:
        print(f"错误: {e}")
        return False

def main():
    config = load_config()
    
    for api_config in config['apis']:
        if api_config['name'] == 'GG公益站':
            # 测试不同长度
            lengths = [500, 2000, 4000, 6000]
            results = []
            
            for length in lengths:
                success = test_message_length(api_config, length)
                results.append((length, success))
                time.sleep(1)  # 避免请求过快
            
            print(f"\n{'='*70}")
            print("测试汇总:")
            for length, success in results:
                status = "✅ 成功" if success else "❌ 失败"
                print(f"  {length} 字符: {status}")
            
            # 找到临界点
            failed_lengths = [l for l, s in results if not s]
            if failed_lengths:
                print(f"\n⚠️ 超过 {min(failed_lengths)} 字符后API返回空响应")

if __name__ == '__main__':
    main()
