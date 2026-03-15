from __future__ import annotations

import json
from typing import Any, Dict, Generator, List, Optional, Tuple

import httpx

from .llm_http import normalize_base_url
from .llm_models import LLMError


def chat_completion(base_url: str, api_key: str, model: str, messages: List[Dict[str, Any]], temperature: float = 0.8, stream: bool = False, timeout_s: float = 60.0) -> Tuple[str, Optional[Generator[str, None, None]]]:
    url = normalize_base_url(base_url) + "/chat/completions"
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    payload: Dict[str, Any] = {"model": model, "messages": messages, "temperature": temperature, "stream": bool(stream)}
    if not stream:
        with httpx.Client(timeout=timeout_s) as client:
            response = client.post(url, headers=headers, json=payload)
        if response.status_code >= 400:
            raise LLMError(f"生成请求失败: HTTP {response.status_code}: {response.text}")
        data = response.json()
        try:
            return str(data["choices"][0]["message"]["content"]), None
        except Exception as exc:
            raise LLMError(f"解析模型响应失败: {data}") from exc
    return "", _iter_stream(url, headers, payload, timeout_s)


def _iter_stream(url: str, headers: Dict[str, str], payload: Dict[str, Any], timeout_s: float) -> Generator[str, None, None]:
    with httpx.Client(timeout=timeout_s) as client:
        with client.stream("POST", url, headers=headers, json=payload) as response:
            if response.status_code >= 400:
                raise LLMError(f"流式生成请求失败: HTTP {response.status_code}: {response.read().decode('utf-8', errors='ignore')}")
            for line in response.iter_lines():
                if not line:
                    continue
                chunk = line[len("data:") :].strip() if line.startswith("data:") else line.strip()
                if chunk == "[DONE]":
                    break
                try:
                    obj = json.loads(chunk)
                    content = (obj["choices"][0].get("delta") or {}).get("content")
                    if content:
                        yield str(content)
                except Exception:
                    continue
