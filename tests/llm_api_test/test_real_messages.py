#!/usr/bin/env python3
"""
使用原项目相同的消息格式测试API
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

def test_with_real_messages(api_config: dict):
    print(f"\n{'='*70}")
    print(f"测试: {api_config['name']}")
    print(f"{'='*70}")
    
    url = normalize_base_url(api_config['base_url']) + "/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_config['api_key']}",
        "Content-Type": "application/json",
    }
    
    # 使用原项目相同的消息格式
    messages = [
        {
            "role": "system",
            "content": """--- charPersonality ---
你是一个擅长中文叙事的互动小说引擎。你的任务是：
1. 根据用户的输入，生成连贯、有趣的剧情
2. 保持角色性格的一致性
3. 提供多样化的选择，让玩家参与剧情发展

--- outputFormat ---
请严格按照以下XML格式输出：

<正文部分>
[在这里写剧情正文，描述场景、对话、动作等]
</正文部分>

<思考过程>
[分析当前局势，思考可能的剧情走向]
</思考过程>

<内容总结>
[简要总结本段剧情的核心内容]
</内容总结>

<行动选项>
<option id="1">[选项1描述]</option>
<option id="2">[选项2描述]</option>
<option id="3">[选项3描述]</option>
</行动选项>"""
        },
        {
            "role": "system",
            "content": """以下是当前故事运行时上下文：
【主角】
- id: CHAR_001  名称: 未知

【世界书（节选）】
- [ability_system] 灵气等级与境界划分: 云泽大陆的修炼者统称为'控灵者'"""
        },
        {
            "role": "user",
            "content": "【追踪小径】对方很可能逃入了迷雾森林，沿小径追踪，但需警惕森林内部的危险（妖兽、磁场）。"
        }
    ]
    
    payload = {
        "model": api_config['model'],
        "messages": messages,
        "temperature": 0.8,
        "stream": True,
    }
    
    print(f"URL: {url}")
    print(f"Model: {api_config['model']}")
    print(f"Messages: {len(messages)}")
    
    # 计算总字符数
    total_chars = sum(len(m['content']) for m in messages)
    print(f"Total message chars: {total_chars}")
    
    stats = {
        "total_lines": 0,
        "content_chunks": 0,
        "total_content": "",
    }
    
    try:
        start = time.time()
        with httpx.Client(timeout=120.0) as client:
            with client.stream("POST", url, headers=headers, json=payload) as r:
                print(f"HTTP状态码: {r.status_code}")
                
                if r.status_code >= 400:
                    text = r.read().decode("utf-8", errors="ignore")
                    print(f"错误响应: {text[:500]}")
                    return
                
                for line in r.iter_lines():
                    stats["total_lines"] += 1
                    
                    if stats["total_lines"] <= 5:
                        print(f"\n[Line {stats['total_lines']}] {line[:300]}")
                    
                    if not line:
                        continue
                    if line.startswith("data:"):
                        chunk = line[len("data:"):].strip()
                    else:
                        chunk = line.strip()
                    
                    if chunk == "[DONE]":
                        print(f"\n收到 [DONE]")
                        break
                    
                    try:
                        obj = json.loads(chunk)
                        choices = obj.get("choices", [])
                        if choices:
                            delta = choices[0].get("delta") or {}
                            content = delta.get("content")
                            if content:
                                stats["content_chunks"] += 1
                                stats["total_content"] += content
                            elif stats["total_lines"] <= 5:
                                print(f"  Delta keys: {list(delta.keys())}")
                            finish_reason = choices[0].get("finish_reason")
                            if finish_reason:
                                print(f"  Finish reason: {finish_reason}")
                    except:
                        pass
                
                elapsed = time.time() - start
                
                print(f"\n{'='*70}")
                print(f"结果:")
                print(f"  总行数: {stats['total_lines']}")
                print(f"  内容块数: {stats['content_chunks']}")
                print(f"  内容长度: {len(stats['total_content'])}")
                print(f"  耗时: {elapsed:.2f}s")
                
                if stats["total_content"]:
                    print(f"\n内容预览:\n{stats['total_content'][:500]}")
                else:
                    print("\n⚠️ 没有收到任何内容!")
                    
    except Exception as e:
        print(f"错误: {e}")
        import traceback
        traceback.print_exc()

def test_simple_message(api_config: dict):
    """测试简单消息是否能正常工作"""
    print(f"\n{'='*70}")
    print(f"简单消息测试: {api_config['name']}")
    print(f"{'='*70}")
    
    url = normalize_base_url(api_config['base_url']) + "/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_config['api_key']}",
        "Content-Type": "application/json",
    }
    
    messages = [
        {"role": "user", "content": "你好，请回复'测试成功'"}
    ]
    
    payload = {
        "model": api_config['model'],
        "messages": messages,
        "temperature": 0.7,
        "stream": True,
    }
    
    print(f"URL: {url}")
    
    content_received = ""
    
    try:
        with httpx.Client(timeout=60.0) as client:
            with client.stream("POST", url, headers=headers, json=payload) as r:
                print(f"HTTP状态码: {r.status_code}")
                
                for line in r.iter_lines():
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
                                print(f"收到: {content[:50]}")
                    except:
                        pass
                
                print(f"\n总内容: {content_received}")
                
    except Exception as e:
        print(f"错误: {e}")

def main():
    config = load_config()
    
    for api_config in config['apis']:
        if api_config['name'] == 'GG公益站':
            test_simple_message(api_config)
            test_with_real_messages(api_config)
    
    print(f"\n{'='*70}")
    print("测试完成")
    print(f"{'='*70}")

if __name__ == '__main__':
    main()
