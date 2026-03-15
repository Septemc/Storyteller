from __future__ import annotations

import json
import re
from typing import List

import httpx

from .llm_models import LLMError


def normalize_base_url(base_url: str) -> str:
    stripped = (base_url or "").rstrip("/")
    return stripped if not stripped or re.search(r"/v1$", stripped) else stripped + "/v1"


def list_models(base_url: str, api_key: str, timeout_s: float = 20.0) -> List[str]:
    if not base_url or not base_url.strip():
        raise LLMError("base_url 不能为空")
    if not api_key or not api_key.strip():
        raise LLMError("api_key 不能为空")
    try:
        with httpx.Client(timeout=timeout_s) as client:
            response = client.get(normalize_base_url(base_url) + "/models", headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"})
        if response.status_code >= 400:
            raise LLMError(f"模型列表请求失败: HTTP {response.status_code}: {response.text[:200]}")
        data = response.json()
        return sorted(set(str(item["id"]) for item in data.get("data") or [] if isinstance(item, dict) and item.get("id")))
    except httpx.TimeoutException as exc:
        raise LLMError(f"请求超时 ({timeout_s}秒)") from exc
    except httpx.RequestError as exc:
        raise LLMError(f"请求错误: {exc}") from exc
    except json.JSONDecodeError as exc:
        raise LLMError(f"响应不是有效的JSON格式: {exc}") from exc
