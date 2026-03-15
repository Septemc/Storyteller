from __future__ import annotations

from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text

from ..base import Base


class StoryRecord(Base):
    __tablename__ = "stories"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(32), ForeignKey("users.user_id"), nullable=True, index=True)
    story_id = Column(String, unique=True, index=True, nullable=False)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    genre_tags_json = Column(Text, nullable=True)
    meta_json = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class SessionBranch(Base):
    __tablename__ = "session_branches"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(32), ForeignKey("users.user_id"), nullable=True, index=True)
    branch_id = Column(String, unique=True, index=True, nullable=False)
    story_id = Column(String, index=True, nullable=False)
    session_id = Column(String, unique=True, index=True, nullable=False)
    parent_branch_id = Column(String, nullable=True, index=True)
    source_segment_id = Column(String, nullable=True, index=True)
    branch_type = Column(String, nullable=False, default="main")
    status = Column(String, nullable=False, default="active")
    active_preset_id = Column(String, nullable=True)
    active_llm_config_id = Column(String, nullable=True)
    active_model = Column(String, nullable=True)
    reasoning_strength = Column(String, nullable=False, default="low")
    summary_short = Column(Text, nullable=True)
    summary_mid = Column(Text, nullable=True)
    last_segment_id = Column(String, nullable=True, index=True)
    meta_json = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class EventLedger(Base):
    __tablename__ = "event_ledger"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(32), ForeignKey("users.user_id"), nullable=True, index=True)
    event_id = Column(String, unique=True, index=True, nullable=False)
    story_id = Column(String, index=True, nullable=False)
    session_id = Column(String, index=True, nullable=False)
    segment_id = Column(String, index=True, nullable=True)
    event_type = Column(String, index=True, nullable=False)
    scope = Column(String, nullable=False, default="session")
    title = Column(String, nullable=False)
    payload_json = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)


class VariableStateSnapshot(Base):
    __tablename__ = "variable_state_snapshots"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(32), ForeignKey("users.user_id"), nullable=True, index=True)
    snapshot_id = Column(String, unique=True, index=True, nullable=False)
    story_id = Column(String, index=True, nullable=False)
    session_id = Column(String, index=True, nullable=False)
    segment_id = Column(String, index=True, nullable=True)
    namespace = Column(String, index=True, nullable=False)
    key = Column(String, index=True, nullable=False)
    value_json = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)


class AgentRunLog(Base):
    __tablename__ = "agent_run_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(32), ForeignKey("users.user_id"), nullable=True, index=True)
    run_id = Column(String, unique=True, index=True, nullable=False)
    story_id = Column(String, index=True, nullable=False)
    session_id = Column(String, index=True, nullable=False)
    segment_id = Column(String, index=True, nullable=True)
    reasoning_strength = Column(String, nullable=False, default="low")
    trace_json = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)


class AgentSegmentLog(Base):
    __tablename__ = "agent_segment_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(32), ForeignKey("users.user_id"), nullable=True, index=True)
    log_id = Column(String, unique=True, index=True, nullable=False)
    story_id = Column(String, index=True, nullable=False)
    session_id = Column(String, index=True, nullable=False)
    segment_id = Column(String, index=True, nullable=False)
    public_log_json = Column(Text, nullable=False)
    developer_log_json = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
