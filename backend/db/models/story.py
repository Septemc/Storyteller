from __future__ import annotations

from datetime import datetime

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String, Text

from ..base import Base


class StorySegment(Base):
    __tablename__ = "story_segments"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(32), ForeignKey("users.user_id"), nullable=True, index=True)
    segment_id = Column(String, unique=True, nullable=False)
    session_id = Column(String, index=True, nullable=False)
    order_index = Column(Integer, nullable=False, default=0)
    user_input = Column(Text, nullable=True)
    text = Column(Text, nullable=False)
    dungeon_id = Column(String, nullable=True)
    dungeon_node_id = Column(String, nullable=True)
    paragraph_word_count = Column(Integer, default=0)
    cumulative_word_count = Column(Integer, default=0)
    frontend_duration = Column(Float, default=0.0)
    backend_duration = Column(Float, default=0.0)
    content_thinking = Column(Text, nullable=True)
    content_story = Column(Text, nullable=True)
    content_summary = Column(Text, nullable=True)
    content_actions = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class Script(Base):
    __tablename__ = "scripts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(32), ForeignKey("users.user_id"), nullable=True, index=True)
    script_id = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    dungeon_ids_json = Column(Text, nullable=True, default="[]")
    meta_json = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class SessionState(Base):
    __tablename__ = "session_state"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(32), ForeignKey("users.user_id"), nullable=True, index=True)
    session_id = Column(String, unique=True, index=True, nullable=False)
    current_script_id = Column(String, nullable=True)
    current_dungeon_id = Column(String, nullable=True)
    current_node_id = Column(String, nullable=True)
    player_position_json = Column(Text, nullable=True)
    global_state_json = Column(Text, nullable=True)
    total_word_count = Column(Integer, default=0)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
