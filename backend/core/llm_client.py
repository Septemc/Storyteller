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


def list_models(base_url: str, api_key: str, timeout_s: float = 20.0) -> List[str]:
    url = _normalize_base_url(base_url) + "/models"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    with httpx.Client(timeout=timeout_s) as client:
        r = client.get(url, headers=headers)
        if r.status_code >= 400:
            raise LLMError(f"模型列表请求失败: HTTP {r.status_code}: {r.text}")
        data = r.json()

    items = data.get("data") or []
    out: List[str] = []
    for it in items:
        if isinstance(it, dict) and it.get("id"):
            out.append(str(it["id"]))
    # 保持稳定顺序
    return sorted(set(out))


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
        with httpx.Client(timeout=timeout_s) as client:
            with client.stream("POST", url, headers=headers, json=payload) as r:
                if r.status_code >= 400:
                    text = r.read().decode("utf-8", errors="ignore")
                    raise LLMError(f"流式生成请求失败: HTTP {r.status_code}: {text}")

                # OpenAI 风格 SSE：
                # data: {json}\n\n
                for line in r.iter_lines():
                    if not line:
                        continue
                    if line.startswith("data:"):
                        chunk = line[len("data:") :].strip()
                    else:
                        chunk = line.strip()

                    if chunk == "[DONE]":
                        break

                    try:
                        obj = json.loads(chunk)
                    except Exception:
                        continue

                    try:
                        delta = obj["choices"][0].get("delta") or {}
                        content = delta.get("content")
                        if content:
                            yield str(content)
                    except Exception:
                        continue

    return "", _iter()
