from __future__ import annotations

from typing import List

import httpx

from .embeddings_config import EmbeddingError


def openai_embeddings(texts: List[str], base_url: str, api_key: str, model: str = "text-embedding-ada-002", timeout_s: float = 60.0) -> List[List[float]]:
    url = base_url.rstrip("/") + "/embeddings"
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    payload = {"model": model, "input": texts}
    try:
        with httpx.Client(timeout=timeout_s) as client:
            response = client.post(url, headers=headers, json=payload)
        if response.status_code >= 400:
            raise EmbeddingError(f"Embedding API 请求失败：HTTP {response.status_code}: {response.text}")
        data = response.json()
        if "data" not in data:
            raise EmbeddingError(f"Embedding API 返回格式错误：{data}")
        embeddings_map = {item["index"]: item["embedding"] for item in data["data"]}
        return [embeddings_map[i] for i in range(len(texts))]
    except httpx.TimeoutException as exc:
        raise EmbeddingError("Embedding API 请求超时") from exc
    except EmbeddingError:
        raise
    except Exception as exc:
        raise EmbeddingError(f"Embedding 计算失败：{exc}") from exc
