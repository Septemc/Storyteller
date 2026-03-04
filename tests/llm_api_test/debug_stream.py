#!/usr/bin/env python3
"""
流式响应调试工具

专门用于调试流式API响应问题，输出详细的原始数据。
"""

import argparse
import json
import sys
import time
import httpx
from pathlib import Path


def debug_stream_response(base_url: str, api_key: str, model: str, message: str, timeout: float = 60.0):
    print(f"\n{'='*70}")
    print(f"调试流式响应")
    print(f"{'='*70}")
    print(f"Base URL: {base_url}")
    print(f"Model: {model}")
    print(f"Message: {message}")
    print(f"{'='*70}\n")
    
    url = base_url.rstrip("/")
    if not url.endswith("/v1"):
        url += "/v1"
    url += "/chat/completions"
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": message}],
        "temperature": 0.7,
        "stream": True,
    }
    
    print(f"请求URL: {url}")
    print(f"请求头: Authorization: Bearer {api_key[:10]}...")
    print(f"请求体: {json.dumps(payload, ensure_ascii=False)}")
    print(f"\n{'='*70}")
    print("开始接收响应...")
    print(f"{'='*70}\n")
    
    try:
        with httpx.Client(timeout=timeout) as client:
            with client.stream("POST", url, headers=headers, json=payload) as r:
                print(f"HTTP状态码: {r.status_code}")
                print(f"响应头: {dict(r.headers)}\n")
                
                if r.status_code >= 400:
                    text = r.read().decode("utf-8", errors="ignore")
                    print(f"错误响应: {text}")
                    return
                
                line_count = 0
                chunk_count = 0
                content_chunks = []
                
                for line in r.iter_lines():
                    line_count += 1
                    
                    print(f"\n--- Line {line_count} ---")
                    print(f"Raw: {line[:500]}{'...' if len(line) > 500 else ''}")
                    
                    if not line:
                        print("(空行，跳过)")
                        continue
                    
                    if line.startswith("data:"):
                        chunk = line[len("data:"):].strip()
                    else:
                        chunk = line.strip()
                    
                    print(f"Chunk: {chunk[:200]}{'...' if len(chunk) > 200 else ''}")
                    
                    if chunk == "[DONE]":
                        print(">>> 收到 [DONE] 信号")
                        break
                    
                    try:
                        obj = json.loads(chunk)
                        print(f"Parsed JSON keys: {list(obj.keys())}")
                        
                        if "choices" in obj:
                            choices = obj["choices"]
                            print(f"Choices count: {len(choices)}")
                            
                            if choices:
                                choice = choices[0]
                                print(f"Choice keys: {list(choice.keys())}")
                                
                                delta = choice.get("delta") or {}
                                print(f"Delta keys: {list(delta.keys())}")
                                
                                content = delta.get("content")
                                if content:
                                    chunk_count += 1
                                    content_chunks.append(content)
                                    print(f">>> Content: {content[:100]}{'...' if len(content) > 100 else ''}")
                                else:
                                    print(">>> No content in delta")
                                    
                                finish_reason = choice.get("finish_reason")
                                if finish_reason:
                                    print(f">>> Finish reason: {finish_reason}")
                        else:
                            print(">>> No 'choices' in response")
                            
                    except json.JSONDecodeError as e:
                        print(f">>> JSON解析失败: {e}")
                
                print(f"\n{'='*70}")
                print("统计信息")
                print(f"{'='*70}")
                print(f"总行数: {line_count}")
                print(f"有效内容块数: {chunk_count}")
                print(f"总内容长度: {sum(len(c) for c in content_chunks)} 字符")
                
                if content_chunks:
                    full_content = "".join(content_chunks)
                    print(f"\n完整内容:")
                    print(f"{full_content[:500]}{'...' if len(full_content) > 500 else ''}")
                else:
                    print("\n⚠️ 未收到任何内容!")
                    
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()


def main():
    parser = argparse.ArgumentParser(description='流式响应调试工具')
    parser.add_argument('--config', '-c', default='config.json', help='配置文件路径')
    parser.add_argument('--api', '-a', required=True, help='API名称')
    parser.add_argument('--message', '-m', default='请输出《兰亭集序》', help='测试消息')
    
    args = parser.parse_args()
    
    config_path = Path(args.config)
    if not config_path.exists():
        print(f"配置文件不存在: {args.config}")
        sys.exit(1)
    
    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    api_config = None
    for api in config['apis']:
        if api['name'] == args.api:
            api_config = api
            break
    
    if not api_config:
        print(f"未找到API配置: {args.api}")
        print(f"可用的API: {[api['name'] for api in config['apis']]}")
        sys.exit(1)
    
    debug_stream_response(
        base_url=api_config['base_url'],
        api_key=api_config['api_key'],
        model=api_config['model'],
        message=args.message
    )


if __name__ == '__main__':
    main()
