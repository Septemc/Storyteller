#!/usr/bin/env python3
"""
完全模拟原项目的请求
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

def test_exact_request(api_config: dict):
    """使用与原项目完全相同的参数"""
    print(f"\n{'='*70}")
    print(f"完全模拟原项目请求: {api_config['name']}")
    print(f"{'='*70}")
    
    url = normalize_base_url(api_config['base_url']) + "/chat/completions"
    
    # 使用与原项目完全相同的headers
    headers = {
        "Authorization": f"Bearer {api_config['api_key']}",
        "Content-Type": "application/json",
    }
    
    # 使用与原项目完全相同的消息
    messages = [
        {
            "role": "system",
            "content": """--- charPersonality ---
你是一个擅长中文叙事的互动小说引擎。你的任务是：
1. 根据用户的输入，生成连贯、有趣的剧情
2. 保持角色性格的一致性
3. 提供多样化的选择，让玩家有参与感
4. 使用生动的描写，营造沉浸感

输出要求：
- 语言风格：现代中文，适当使用成语和修辞
- 剧情节奏：张弛有度，避免过于平淡或过于紧凑
- 互动性：每次输出后提供3-5个行动选项

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
- [ability_system] 灵气等级与境界划分: 云泽大陆的修炼者统称为'控灵者'。境界分为：
1. 纳灵境：感应天地灵气，开辟丹田。
2. 筑元境：灵气化液，铸就根基。
3. 破虚境：神识出窍，可短距离瞬移。
4. 登神阶：触碰法则，寿元达千载。
每个境界分为九重小境界，突破难度递增。"""
        },
        {
            "role": "user",
            "content": "【追踪小径】对方很可能逃入了迷雾森林，沿小径追踪，但需警惕森林内部的危险（妖兽、磁场）。"
        }
    ]
    
    # 使用与原项目完全相同的payload
    payload = {
        "model": api_config['model'],
        "messages": messages,
        "temperature": 0.8,
        "stream": True,
    }
    
    print(f"URL: {url}")
    print(f"Model: {api_config['model']}")
    print(f"Timeout: 120s")
    
    total_chars = sum(len(m['content']) for m in messages)
    print(f"Total message chars: {total_chars}")
    
    # 打印payload（不包含完整内容）
    payload_preview = {
        "model": payload["model"],
        "messages": [{"role": m["role"], "content_len": len(m["content"])} for m in messages],
        "temperature": payload["temperature"],
        "stream": payload["stream"]
    }
    print(f"Payload: {json.dumps(payload_preview, ensure_ascii=False)}")
    
    content_received = ""
    line_count = 0
    raw_lines = []
    
    try:
        start = time.time()
        with httpx.Client(timeout=120.0) as client:
            with client.stream("POST", url, headers=headers, json=payload) as r:
                print(f"\nHTTP状态码: {r.status_code}")
                print(f"响应头 Content-Type: {r.headers.get('content-type')}")
                
                if r.status_code >= 400:
                    text = r.read().decode("utf-8", errors="ignore")
                    print(f"错误响应: {text[:500]}")
                    return
                
                for line in r.iter_lines():
                    line_count += 1
                    if line_count <= 5:
                        raw_lines.append(line[:300])
                        print(f"\n[Line {line_count}] {line[:300]}")
                    
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
                                content_received += content
                            finish_reason = choices[0].get("finish_reason")
                            if finish_reason:
                                print(f"  Finish reason: {finish_reason}")
                    except Exception as e:
                        if line_count <= 5:
                            print(f"  Parse error: {e}")
                
                elapsed = time.time() - start
                
                print(f"\n{'='*70}")
                print(f"结果:")
                print(f"  总行数: {line_count}")
                print(f"  内容长度: {len(content_received)}")
                print(f"  耗时: {elapsed:.1f}s")
                
                if content_received:
                    print(f"\n内容预览:\n{content_received[:500]}")
                else:
                    print("\n⚠️ 没有收到任何内容!")
                    print("\n前5行原始数据:")
                    for i, line in enumerate(raw_lines, 1):
                        print(f"  {i}: {line}")
                    
    except Exception as e:
        print(f"\n错误: {e}")
        import traceback
        traceback.print_exc()

def main():
    config = load_config()
    
    for api_config in config['apis']:
        if api_config['name'] == 'GG公益站':
            test_exact_request(api_config)

if __name__ == '__main__':
    main()
