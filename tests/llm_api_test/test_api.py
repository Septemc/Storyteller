#!/usr/bin/env python3
"""
LLM API 测试工具

功能：
1. 测试API连接性
2. 测试非流式生成
3. 测试流式生成
4. 详细调试输出
5. 错误场景模拟

使用方法：
  python test_api.py                    # 运行所有测试
  python test_api.py --config config.json  # 指定配置文件
  python test_api.py --api DeepSeek     # 测试指定API
  python test_api.py --debug            # 开启调试模式
"""

import argparse
import json
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional

from llm_client import LLMError, chat_completion, list_models


class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'


def print_header(text: str):
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*60}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{text}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'='*60}{Colors.ENDC}\n")


def print_success(text: str):
    print(f"{Colors.OKGREEN}✅ {text}{Colors.ENDC}")


def print_error(text: str):
    print(f"{Colors.FAIL}❌ {text}{Colors.ENDC}")


def print_warning(text: str):
    print(f"{Colors.WARNING}⚠️ {text}{Colors.ENDC}")


def print_info(text: str):
    print(f"{Colors.OKCYAN}ℹ️ {text}{Colors.ENDC}")


def print_debug(text: str, debug: bool = False):
    if debug:
        print(f"{Colors.OKBLUE}[DEBUG] {text}{Colors.ENDC}")


def load_config(config_path: str) -> Dict:
    path = Path(config_path)
    if not path.exists():
        print_error(f"配置文件不存在: {config_path}")
        print_info("请复制 config.example.json 为 config.json 并填入API密钥")
        sys.exit(1)
    
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def test_list_models(api_config: Dict, debug: bool = False) -> bool:
    print_header(f"测试模型列表 - {api_config['name']}")
    
    try:
        print_info(f"Base URL: {api_config['base_url']}")
        models = list_models(
            base_url=api_config['base_url'],
            api_key=api_config['api_key'],
            timeout_s=30.0
        )
        print_success(f"获取到 {len(models)} 个模型")
        if debug:
            for m in models[:10]:
                print_debug(f"  - {m}", debug)
            if len(models) > 10:
                print_debug(f"  ... 还有 {len(models) - 10} 个模型", debug)
        return True
    except LLMError as e:
        print_error(f"获取模型列表失败: {e}")
        return False
    except Exception as e:
        print_error(f"未知错误: {e}")
        return False


def test_non_stream(api_config: Dict, test_message: str, debug: bool = False) -> bool:
    print_header(f"测试非流式生成 - {api_config['name']}")
    
    messages = [{"role": "user", "content": test_message}]
    
    try:
        print_info(f"Model: {api_config['model']}")
        print_info(f"Message: {test_message}")
        print_debug(f"Payload: {json.dumps({'model': api_config['model'], 'messages': messages}, ensure_ascii=False)}", debug)
        
        start_time = time.time()
        full_text, _ = chat_completion(
            base_url=api_config['base_url'],
            api_key=api_config['api_key'],
            model=api_config['model'],
            messages=messages,
            temperature=0.7,
            stream=False,
            timeout_s=60.0
        )
        elapsed = time.time() - start_time
        
        print_success(f"生成成功 (耗时: {elapsed:.2f}s)")
        print_info(f"响应长度: {len(full_text)} 字符")
        print_info(f"响应内容: {full_text[:200]}{'...' if len(full_text) > 200 else ''}")
        return True
        
    except LLMError as e:
        print_error(f"生成失败: {e}")
        return False
    except Exception as e:
        print_error(f"未知错误: {e}")
        return False


def test_stream(api_config: Dict, test_message: str, debug: bool = False) -> bool:
    print_header(f"测试流式生成 - {api_config['name']}")
    
    messages = [{"role": "user", "content": test_message}]
    
    try:
        print_info(f"Model: {api_config['model']}")
        print_info(f"Message: {test_message}")
        
        start_time = time.time()
        _, stream_gen = chat_completion(
            base_url=api_config['base_url'],
            api_key=api_config['api_key'],
            model=api_config['model'],
            messages=messages,
            temperature=0.7,
            stream=True,
            timeout_s=60.0
        )
        
        if stream_gen is None:
            print_error("流式生成器为空")
            return False
        
        print_info("开始接收流式数据...")
        
        full_content = ""
        chunk_count = 0
        
        for delta in stream_gen:
            chunk_count += 1
            full_content += delta
            if debug and chunk_count <= 5:
                print_debug(f"Chunk {chunk_count}: {delta[:50]}{'...' if len(delta) > 50 else ''}", debug)
        
        elapsed = time.time() - start_time
        
        print_success(f"流式生成完成 (耗时: {elapsed:.2f}s)")
        print_info(f"接收到 {chunk_count} 个数据块")
        print_info(f"响应长度: {len(full_content)} 字符")
        print_info(f"响应内容: {full_content[:200]}{'...' if len(full_content) > 200 else ''}")
        
        if chunk_count == 0:
            print_warning("警告: 收到0个数据块，API可能不支持真正的流式传输")
        
        return len(full_content) > 0
        
    except LLMError as e:
        print_error(f"生成失败: {e}")
        return False
    except Exception as e:
        print_error(f"未知错误: {e}")
        return False


def test_error_handling(api_config: Dict, debug: bool = False) -> bool:
    print_header(f"测试错误处理 - {api_config['name']}")
    
    print_info("测试1: 无效API密钥")
    try:
        _, _ = chat_completion(
            base_url=api_config['base_url'],
            api_key="invalid_key_12345",
            model=api_config['model'],
            messages=[{"role": "user", "content": "test"}],
            stream=False,
            timeout_s=10.0
        )
        print_warning("预期应该失败，但成功了")
    except LLMError as e:
        print_success(f"正确捕获错误: {str(e)[:100]}")
    except Exception as e:
        print_success(f"捕获异常: {str(e)[:100]}")
    
    print_info("测试2: 无效模型名称")
    try:
        _, _ = chat_completion(
            base_url=api_config['base_url'],
            api_key=api_config['api_key'],
            model="nonexistent-model-xyz",
            messages=[{"role": "user", "content": "test"}],
            stream=False,
            timeout_s=10.0
        )
        print_warning("预期应该失败，但成功了")
    except LLMError as e:
        print_success(f"正确捕获错误: {str(e)[:100]}")
    except Exception as e:
        print_success(f"捕获异常: {str(e)[:100]}")
    
    print_info("测试3: 无效Base URL")
    try:
        _, _ = chat_completion(
            base_url="https://invalid-url-12345.com",
            api_key=api_config['api_key'],
            model=api_config['model'],
            messages=[{"role": "user", "content": "test"}],
            stream=False,
            timeout_s=5.0
        )
        print_warning("预期应该失败，但成功了")
    except Exception as e:
        print_success(f"正确捕获连接错误: {str(e)[:100]}")
    
    return True


def run_all_tests(config: Dict, api_filter: Optional[str] = None, debug: bool = False):
    results = []
    test_message = config.get('test_settings', {}).get('test_message', '请回复：测试成功')
    
    for api_config in config['apis']:
        if api_filter and api_config['name'] != api_filter:
            continue
        
        api_result = {
            'name': api_config['name'],
            'models': False,
            'non_stream': False,
            'stream': False,
            'error_handling': False
        }
        
        print(f"\n{'#'*60}")
        print(f"# API: {api_config['name']}")
        print(f"# Base URL: {api_config['base_url']}")
        print(f"# Model: {api_config['model']}")
        print(f"{'#'*60}")
        
        api_result['models'] = test_list_models(api_config, debug)
        api_result['non_stream'] = test_non_stream(api_config, test_message, debug)
        api_result['stream'] = test_stream(api_config, test_message, debug)
        api_result['error_handling'] = test_error_handling(api_config, debug)
        
        results.append(api_result)
    
    print_header("测试汇总")
    
    for r in results:
        status = "✅" if all([r['non_stream'], r['stream']]) else "❌"
        print(f"\n{status} {r['name']}")
        print(f"   模型列表: {'✅' if r['models'] else '❌'}")
        print(f"   非流式: {'✅' if r['non_stream'] else '❌'}")
        print(f"   流式: {'✅' if r['stream'] else '❌'}")
        print(f"   错误处理: {'✅' if r['error_handling'] else '❌'}")
    
    return results


def main():
    parser = argparse.ArgumentParser(description='LLM API 测试工具')
    parser.add_argument('--config', '-c', default='config.json', help='配置文件路径')
    parser.add_argument('--api', '-a', help='指定要测试的API名称')
    parser.add_argument('--debug', '-d', action='store_true', help='开启调试模式')
    parser.add_argument('--quick', '-q', action='store_true', help='快速测试（仅测试非流式）')
    
    args = parser.parse_args()
    
    print(f"\n{Colors.BOLD}LLM API 测试工具{Colors.ENDC}")
    print(f"配置文件: {args.config}")
    print(f"调试模式: {'开启' if args.debug else '关闭'}")
    
    config = load_config(args.config)
    
    if args.quick:
        for api_config in config['apis']:
            if args.api and api_config['name'] != args.api:
                continue
            test_non_stream(api_config, config.get('test_settings', {}).get('test_message', 'test'), args.debug)
    else:
        run_all_tests(config, args.api, args.debug)


if __name__ == '__main__':
    main()
