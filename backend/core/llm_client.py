"""OpenAI-compatible LLM client.

支持：
- models list: GET {base_url}/v1/models
- chat completion: POST {base_url}/v1/chat/completions

base_url 允许用户输入：
- https://api.openai.com
- https://api.openai.com/v1
- http://localhost:8000
等。
模块会自动补齐 /v1。
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any, Dict, Generator, Iterable, List, Optional, Tuple

import httpx


def _normalize_base_url(base_url: str) -> str:
    s = (base_url or "").rstrip("/")
    if not s:
        return s
    # 若已包含 /v1，则保持
    if re.search(r"/v1$", s):
        return s
    return s + "/v1"


@dataclass
class LLMApiConfig:
    id: str
    name: str
    base_url: str
    api_key: str
    stream: bool = True
    default_model: Optional[str] = None


class LLMError(RuntimeError):
    pass



def _clean_error_body(body: str, limit: int = 180) -> str:
    text = (body or '').strip()
    if not text:
        return ''
    lowered = text.lower()
    if '<!doctype html' in lowered or '<html' in lowered:
        title_start = lowered.find('<title>')
        title_end = lowered.find('</title>')
        if title_start != -1 and title_end != -1 and title_end > title_start:
            title = text[title_start + 7:title_end].strip()
            return title[:limit]
        return '??????? HTML ???'
    text = re.sub(r'\s+', ' ', text)
    return text[:limit]


def _summarize_http_error(status_code: int, body: str, *, stream: bool = False) -> str:
    prefix = '????????' if stream else '??????'
    cleaned = _clean_error_body(body)
    lowered = (body or '').lower()
    if status_code == 520 or 'cloudflare' in lowered:
        return f'{prefix}: ??????????? (HTTP {status_code})????????? base_url?'
    if cleaned:
        return f'{prefix}: HTTP {status_code}: {cleaned}'
    return f'{prefix}: HTTP {status_code}'


def list_models(base_url: str, api_key: str, timeout_s: float = 20.0) -> List[str]:
    """获取可用模型列表，包含完整的异常处理"""
    try:
        # 验证输入参数
        if not base_url or not base_url.strip():
            raise LLMError("base_url 不能为空")
        
        if not api_key or not api_key.strip():
            raise LLMError("api_key 不能为空")
        
        url = _normalize_base_url(base_url) + "/models"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        
        # 添加详细的调试信息
        print(f"[LLM_DEBUG] 请求模型列表: {url}")
        
        with httpx.Client(timeout=timeout_s) as client:
            r = client.get(url, headers=headers)
            
            if r.status_code >= 400:
                error_detail = f"模型列表请求失败: HTTP {r.status_code}"
                if r.text:
                    error_detail += f": {r.text[:200]}"  # 限制错误信息长度
                raise LLMError(error_detail)
            
            # 验证响应格式
            try:
                data = r.json()
            except json.JSONDecodeError as e:
                raise LLMError(f"响应不是有效的JSON格式: {str(e)}")

        items = data.get("data") or []
        out: List[str] = []
        for it in items:
            if isinstance(it, dict) and it.get("id"):
                out.append(str(it["id"]))
        
        # 保持稳定顺序
        return sorted(set(out))
        
    except httpx.TimeoutException:
        raise LLMError(f"请求超时 ({timeout_s}秒)")
    except httpx.ConnectError as e:
        raise LLMError(f"连接失败: {str(e)}")
    except httpx.RequestError as e:
        raise LLMError(f"请求错误: {str(e)}")
    except Exception as e:
        # 捕获所有其他异常，避免500错误
        raise LLMError(f"获取模型列表时发生未知错误: {str(e)}")


def chat_completion(
    base_url: str,
    api_key: str,
    model: str,
    messages: List[Dict[str, Any]],
    temperature: float = 0.8,
    stream: bool = False,
    timeout_s: float = 60.0,
) -> Tuple[str, Optional[Generator[str, None, None]]]:
    """返回 (full_text, stream_gen)

    - stream=False: full_text 有值，stream_gen=None
    - stream=True: full_text=""，stream_gen 逐段产出 delta text
    """
    url = _normalize_base_url(base_url) + "/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    payload: Dict[str, Any] = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "stream": bool(stream),
    }

    print(f"[LLM_DEBUG] chat_completion called:")
    print(f"  base_url: {base_url}")
    print(f"  model: '{model}'")
    print(f"  stream: {stream}")
    print(f"  messages count: {len(messages)}")
    for i, msg in enumerate(messages):
        content = msg.get("content", "")
        # preview = content[:200] + "..." if len(content) > 200 else content
        print(f"  message[{i}] role={msg.get('role')}, len={len(content)}:")
        # print(f"    {preview}")
    
    print(f"[LLM_DEBUG] Payload JSON size: {len(json.dumps(payload, ensure_ascii=False))} bytes")

    if not stream:
        with httpx.Client(timeout=timeout_s) as client:
            r = client.post(url, headers=headers, json=payload)
            if r.status_code >= 400:
                raise LLMError(f"生成请求失败: HTTP {r.status_code}: {r.text}")
            data = r.json()
        try:
            return str(data["choices"][0]["message"]["content"]), None
        except Exception:
            raise LLMError(f"解析模型响应失败: {data}")

    def _iter() -> Generator[str, None, None]:
        chunk_count = 0
        raw_line_count = 0
        with httpx.Client(timeout=timeout_s) as client:
            with client.stream("POST", url, headers=headers, json=payload) as r:
                print(f"[LLM_DEBUG] Stream response status: {r.status_code}")
                if r.status_code >= 400:
                    text = r.read().decode("utf-8", errors="ignore")
                    raise LLMError(f"流式生成请求失败: HTTP {r.status_code}: {text}")

                for line in r.iter_lines():
                    raw_line_count += 1
                    if raw_line_count <= 5:
                        print(f"[LLM_DEBUG] Raw line {raw_line_count}: {line[:200]}")
                    
                    if not line:
                        continue
                    if line.startswith("data:"):
                        chunk = line[len("data:") :].strip()
                    else:
                        chunk = line.strip()

                    if chunk == "[DONE]":
                        print(f"[LLM_DEBUG] Stream done, total chunks: {chunk_count}, raw lines: {raw_line_count}")
                        break

                    try:
                        obj = json.loads(chunk)
                    except Exception as e:
                        if raw_line_count <= 5:
                            print(f"[LLM_DEBUG] JSON parse error: {e}")
                        continue

                    try:
                        delta = obj["choices"][0].get("delta") or {}
                        content = delta.get("content")
                        if content:
                            chunk_count += 1
                            yield str(content)
                        elif raw_line_count <= 5:
                            print(f"[LLM_DEBUG] Delta keys: {list(delta.keys())}")
                    except Exception as e:
                        if raw_line_count <= 5:
                            print(f"[LLM_DEBUG] Extract content error: {e}")
                        continue
                
                print(f"[LLM_DEBUG] Stream finished, yielded {chunk_count} chunks, total raw lines: {raw_line_count}")

    return "", _iter()
