from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


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
