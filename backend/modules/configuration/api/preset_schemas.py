from __future__ import annotations

from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class PresetIn(BaseModel):
    id: Optional[str] = None
    name: str = Field(default="未命名预设")
    version: int = 1
    root: Dict[str, Any]
    meta: Dict[str, Any] = Field(default_factory=dict)
