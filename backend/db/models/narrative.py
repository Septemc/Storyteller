from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import relationship

from ..base import Base
from .common import generate_worldbook_id


class WorldbookEntry(Base):
    __tablename__ = "worldbook"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(32), ForeignKey("users.user_id"), nullable=True, index=True)
    worldbook_id = Column(String(8), nullable=False, index=True, default=generate_worldbook_id)
    entry_id = Column(String, unique=True, index=True, nullable=False)
    category = Column(String, index=True, nullable=True)
    tags = Column(String, nullable=True)
    title = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    importance = Column(Float, default=0.5)
    canonical = Column(Boolean, default=False)
    meta_json = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Dungeon(Base):
    __tablename__ = "dungeons"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(32), ForeignKey("users.user_id"), nullable=True, index=True)
    dungeon_id = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    level_min = Column(Integer, nullable=True)
    level_max = Column(Integer, nullable=True)
    global_rules_json = Column(Text, nullable=True)

    nodes = relationship(
        "DungeonNode",
        back_populates="dungeon",
        cascade="all, delete-orphan",
        order_by="DungeonNode.index_in_dungeon",
    )


class DungeonNode(Base):
    __tablename__ = "dungeon_nodes"

    id = Column(Integer, primary_key=True, index=True)
    dungeon_id = Column(String, ForeignKey("dungeons.dungeon_id"), nullable=False)
    node_id = Column(String, nullable=False)
    index_in_dungeon = Column(Integer, nullable=False, default=0)
    name = Column(String, nullable=False)
    progress_percent = Column(Integer, nullable=True)
    entry_conditions_json = Column(Text, nullable=True)
    exit_conditions_json = Column(Text, nullable=True)
    summary_requirements = Column(Text, nullable=True)
    story_requirements_json = Column(Text, nullable=True)
    branching_json = Column(Text, nullable=True)

    dungeon = relationship("Dungeon", back_populates="nodes")


class CharacterTemplate(Base):
    __tablename__ = "character_templates"
    __table_args__ = (UniqueConstraint("session_id", "template_id", name="uq_character_templates_session_template"),)

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(32), ForeignKey("users.user_id"), nullable=True, index=True)
    session_id = Column(String, nullable=False, index=True)
    template_id = Column(String, nullable=False, index=True)
    template_name = Column(String, nullable=False)
    template_json = Column(Text, nullable=False, default="{}")
    is_active = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Character(Base):
    __tablename__ = "characters"
    __table_args__ = (UniqueConstraint("session_id", "character_id", name="uq_characters_session_character"),)

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(32), ForeignKey("users.user_id"), nullable=True, index=True)
    session_id = Column(String, nullable=False, index=True)
    template_id = Column(String, nullable=True)
    character_id = Column(String, index=True, nullable=False)
    data_json = Column(Text, nullable=False, default="{}")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class GlobalSetting(Base):
    __tablename__ = "global_settings"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(32), ForeignKey("users.user_id"), nullable=True, index=True)
    key = Column(String, unique=True, nullable=False)
    value_json = Column(Text, nullable=False)
