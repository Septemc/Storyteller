from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text

from ..base import Base
from .common import generate_worldbook_id


class DBPreset(Base):
    __tablename__ = "presets"

    id = Column(String, primary_key=True, index=True)
    user_id = Column(String(32), ForeignKey("users.user_id"), nullable=True, index=True)
    name = Column(String, index=True, nullable=False)
    version = Column(Integer, default=1)
    is_active = Column(Boolean, default=False)
    is_default = Column(Boolean, default=False)
    config_json = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class DBLLMConfig(Base):
    __tablename__ = "llm_configs"

    id = Column(String, primary_key=True, index=True)
    user_id = Column(String(32), ForeignKey("users.user_id"), nullable=True, index=True)
    name = Column(String, nullable=False)
    base_url = Column(String, nullable=False)
    api_key = Column(String, nullable=False)
    stream = Column(Boolean, default=True)
    default_model = Column(String, nullable=True)
    is_active = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class DBRegexProfile(Base):
    __tablename__ = "regexs"

    id = Column(String, primary_key=True, index=True)
    user_id = Column(String(32), ForeignKey("users.user_id"), nullable=True, index=True)
    name = Column(String, index=True, nullable=False)
    version = Column(Integer, default=1)
    is_default = Column(Boolean, default=False)
    is_active = Column(Boolean, default=False)
    config_json = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class WorldbookEmbedding(Base):
    __tablename__ = "worldbook_embeddings"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(32), ForeignKey("users.user_id"), nullable=True, index=True)
    worldbook_id = Column(String(8), nullable=False, index=True, default=generate_worldbook_id)
    entry_id = Column(String, ForeignKey("worldbook.entry_id"), nullable=False, index=True)
    embedding_json = Column(Text, nullable=False)
    content_hash = Column(String, nullable=False, index=True)
    embedding_model = Column(String, nullable=False)
    dimension = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
