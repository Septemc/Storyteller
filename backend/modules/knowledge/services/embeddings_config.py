from __future__ import annotations

import hashlib
from dataclasses import dataclass


@dataclass
class EmbeddingConfig:
    provider: str = "openai"
    model: str | None = None
    base_url: str | None = None
    api_key: str | None = None
    dimension: int = 768


class EmbeddingError(RuntimeError):
    pass


def normalize_text(text: str) -> str:
    return " ".join((text or "").split())


def text_hash(text: str) -> str:
    return hashlib.md5(text.encode("utf-8")).hexdigest()
