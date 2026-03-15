from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


class LLMConfigIn(BaseModel):
    id: Optional[str] = None
    name: str = Field(default='未命名配置')
    base_url: str
    api_key: str
    stream: bool = True
    default_model: Optional[str] = None


class LLMConfigOut(LLMConfigIn):
    id: str


class ActiveLLM(BaseModel):
    config_id: Optional[str] = None
    model: Optional[str] = None


class ListModelsReq(BaseModel):
    base_url: str
    api_key: str
