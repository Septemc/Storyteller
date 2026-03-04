#!/usr/bin/env python3
"""
对比测试脚本 - 分析两种API的响应差异
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

def test_non_stream(api_config: dict):
    print(f"\n{'='*70}")
    print(f"非流式测试: {api_config['name']}")
    print(f"{'='*70}")
    
    url = normalize_base_url(api_config['base_url']) + "/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_config['api_key']}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": api_config['model'],
        "messages": [{"role": "user", "content": "请说'测试成功'"}],
        "temperature": 0.7,
        "stream": False,
    }
    
    print(f"URL: {url}")
    print(f"Model: {api_config['model']}")
    
    try:
        start = time.time()
        with httpx.Client(timeout=60.0) as client:
            r = client.post(url, headers=headers, json=payload)
            elapsed = time.time() - start
            
            print(f"HTTP状态码: {r.status_code}")
            print(f"耗时: {elapsed:.2f}s")
            
            if r.status_code >= 400:
                print(f"错误响应: {r.text[:500]}")
                return
            
            data = r.json()
            print(f"\n响应结构:")
            print(f"  顶层keys: {list(data.keys())}")
            
            if "choices" in data:
                print(f"  choices数量: {len(data['choices'])}")
                if data['choices']:
                    choice = data['choices'][0]
                    print(f"  choice keys: {list(choice.keys())}")
                    
                    message = choice.get("message", {})
                    print(f"  message keys: {list(message.keys())}")
                    
                    content = message.get("content", "")
                    print(f"\n  content长度: {len(content)}")
                    print(f"  content预览: {content[:200]}{'...' if len(content) > 200 else ''}")
                    
                    if "reasoning_content" in message:
                        rc = message["reasoning_content"]
                        print(f"\n  reasoning_content长度: {len(rc)}")
                        print(f"  reasoning_content预览: {rc[:200]}{'...' if len(rc) > 200 else ''}")
    except Exception as e:
        print(f"错误: {e}")
        import traceback
        traceback.print_exc()

def test_stream_detailed(api_config: dict):
    print(f"\n{'='*70}")
    print(f"流式测试(详细): {api_config['name']}")
    print(f"{'='*70}")
    
    url = normalize_base_url(api_config['base_url']) + "/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_config['api_key']}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": api_config['model'],
        "messages": [{"role": "user", "content": "请说'测试成功'"}],
        "temperature": 0.7,
        "stream": True,
    }
    
    print(f"URL: {url}")
    print(f"Model: {api_config['model']}")
    
    stats = {
        "total_lines": 0,
        "empty_lines": 0,
        "done_signals": 0,
        "json_parse_errors": 0,
        "no_choices": 0,
        "no_delta": 0,
        "no_content": 0,
        "has_reasoning": 0,
        "has_content": 0,
        "content_chunks": [],
        "reasoning_chunks": [],
    }
    
    try:
        start = time.time()
        with httpx.Client(timeout=60.0) as client:
            with client.stream("POST", url, headers=headers, json=payload) as r:
                print(f"HTTP状态码: {r.status_code}")
                
                if r.status_code >= 400:
                    text = r.read().decode("utf-8", errors="ignore")
                    print(f"错误响应: {text[:500]}")
                    return
                
                for line in r.iter_lines():
                    stats["total_lines"] += 1
                    
                    if not line:
                        stats["empty_lines"] += 1
                        continue
                    
                    if line.startswith("data:"):
                        chunk = line[len("data:"):].strip()
                    else:
                        chunk = line.strip()
                    
                    if chunk == "[DONE]":
                        stats["done_signals"] += 1
                        print(f"\n[Line {stats['total_lines']}] 收到 [DONE]")
                        continue
                    
                    try:
                        obj = json.loads(chunk)
                    except json.JSONDecodeError as e:
                        stats["json_parse_errors"] += 1
                        print(f"\n[Line {stats['total_lines']}] JSON解析失败: {e}")
                        print(f"  原始: {chunk[:100]}")
                        continue
                    
                    choices = obj.get("choices", [])
                    if not choices:
                        stats["no_choices"] += 1
                        print(f"\n[Line {stats['total_lines']}] 无choices字段")
                        continue
                    
                    delta = choices[0].get("delta")
                    if not delta:
                        stats["no_delta"] += 1
                        continue
                    
                    delta_keys = list(delta.keys()) if isinstance(delta, dict) else []
                    
                    if "reasoning_content" in delta:
                        stats["has_reasoning"] += 1
                        rc = delta["reasoning_content"]
                        stats["reasoning_chunks"].append(rc)
                        if stats["has_reasoning"] <= 2:
                            print(f"\n[Line {stats['total_lines']}] reasoning_content: {rc[:50]}...")
                    
                    if "content" in delta:
                        content = delta["content"]
                        if content:
                            stats["has_content"] += 1
                            stats["content_chunks"].append(content)
                            if stats["has_content"] <= 3:
                                print(f"\n[Line {stats['total_lines']}] content: {content[:50]}...")
                    else:
                        if delta_keys and stats["no_content"] < 3:
                            print(f"\n[Line {stats['total_lines']}] delta无content, keys: {delta_keys}")
                        stats["no_content"] += 1
                
                elapsed = time.time() - start
                
                print(f"\n{'='*70}")
                print("统计结果:")
                print(f"{'='*70}")
                print(f"总行数: {stats['total_lines']}")
                print(f"空行数: {stats['empty_lines']}")
                print(f"DONE信号: {stats['done_signals']}")
                print(f"JSON解析错误: {stats['json_parse_errors']}")
                print(f"无choices: {stats['no_choices']}")
                print(f"无delta: {stats['no_delta']}")
                print(f"有reasoning_content: {stats['has_reasoning']}")
                print(f"有content: {stats['has_content']}")
                print(f"无content的delta: {stats['no_content']}")
                print(f"\n总耗时: {elapsed:.2f}s")
                
                total_content = "".join(stats["content_chunks"])
                total_reasoning = "".join(stats["reasoning_chunks"])
                
                print(f"\n内容总长度: {len(total_content)} 字符")
                print(f"思考过程总长度: {len(total_reasoning)} 字符")
                
                if total_content:
                    print(f"\n内容预览: {total_content[:200]}")
                else:
                    print("\n⚠️ 没有收到任何content内容!")
                    
    except Exception as e:
        print(f"错误: {e}")
        import traceback
        traceback.print_exc()

def main():
    config = load_config()
    
    for api_config in config['apis']:
        if api_config['name'] in ['DeepSeek', 'GG公益站']:
            test_non_stream(api_config)
            test_stream_detailed(api_config)
    
    print(f"\n{'='*70}")
    print("测试完成")
    print(f"{'='*70}")

if __name__ == '__main__':
    main()
