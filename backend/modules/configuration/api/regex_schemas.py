from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class RegexProfileCreate(BaseModel):
    name: str
    rules: List[Dict[str, Any]] = Field(default_factory=list)


class RegexProfileUpdate(BaseModel):
    name: Optional[str] = None
    rules: Optional[List[Dict[str, Any]]] = None


class RegexProfileResponse(BaseModel):
    id: str
    name: str
    version: int
    is_default: bool = False
    is_active: bool = False
    rules: List[Dict[str, Any]] = Field(default_factory=list)


class RegexProfileListItem(BaseModel):
    id: str
    name: str
    version: int
    is_default: bool = False
    is_active: bool = False
