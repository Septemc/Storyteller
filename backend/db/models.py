from datetime import datetime
from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    Boolean,
    Float,
    DateTime,
    ForeignKey,
)
from sqlalchemy.orm import relationship
from .base import Base


class WorldbookEntry(Base):
    __tablename__ = "worldbook_entries"

    id = Column(Integer, primary_key=True, index=True)
    entry_id = Column(String, unique=True, index=True, nullable=False)
    category = Column(String, index=True, nullable=True)
    tags = Column(String, nullable=True)  # 逗号分隔存储
    title = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    importance = Column(Float, default=0.5)
    canonical = Column(Boolean, default=False)
    meta_json = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )


class Dungeon(Base):
    __tablename__ = "dungeons"

    id = Column(Integer, primary_key=True, index=True)
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
    """
    [新增] 角色模板表
    存储自定义的 Tabs 和 Fields 结构
    """
    __tablename__ = "character_templates"

    id = Column(String, primary_key=True, index=True)  # 例如: "cultivation_v1"
    name = Column(String, nullable=False)  # 例如: "修仙人物模板"
    description = Column(String, nullable=True)
    # 核心配置：{ "tabs": [...], "fields": [...] }
    config_json = Column(Text, nullable=False, default="{}")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Character(Base):
    __tablename__ = "characters"

    id = Column(Integer, primary_key=True, index=True)
    character_id = Column(String, unique=True, index=True, nullable=False)

    # [新增] 绑定模板 ID，默认为 'system_default'
    template_id = Column(String, default="system_default", nullable=True)

    type = Column(String, nullable=False, default="npc")

    # [新增] 动态数据存储：所有自定义字段的内容都存这里
    # 未来可逐步废弃 basic_json, knowledge_json 等
    data_json = Column(Text, nullable=True)

    # ... (为了兼容现有数据，保留旧字段，暂不删除) ...
    basic_json = Column(Text, nullable=True)
    knowledge_json = Column(Text, nullable=True)
    secrets_json = Column(Text, nullable=True)
    attributes_json = Column(Text, nullable=True)
    relations_json = Column(Text, nullable=True)
    equipment_json = Column(Text, nullable=True)
    items_json = Column(Text, nullable=True)
    skills_json = Column(Text, nullable=True)
    fortune_json = Column(Text, nullable=True)

    meta_json = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class GlobalSetting(Base):
    __tablename__ = "global_settings"

    id = Column(Integer, primary_key=True, index=True)
    key = Column(String, unique=True, nullable=False)
    value_json = Column(Text, nullable=False)


class StorySegment(Base):
    __tablename__ = "story_segments"

    id = Column(Integer, primary_key=True, index=True)
    segment_id = Column(String, unique=True, nullable=False)
    session_id = Column(String, index=True, nullable=False)
    order_index = Column(Integer, nullable=False, default=0)
    text = Column(Text, nullable=False)
    dungeon_id = Column(String, nullable=True)
    dungeon_node_id = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class SessionState(Base):
    __tablename__ = "session_state"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String, unique=True, index=True, nullable=False)
    current_dungeon_id = Column(String, nullable=True)
    current_node_id = Column(String, nullable=True)
    player_position_json = Column(Text, nullable=True)
    global_state_json = Column(Text, nullable=True)
    total_word_count = Column(Integer, default=0)
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )


class DBPreset(Base):
    """
    [新增] 预设表
    存储完整的提示词树结构 (JSON)
    """
    __tablename__ = "presets"

    id = Column(String, primary_key=True, index=True)  # 使用 UUID 字符串
    name = Column(String, index=True, nullable=False)
    version = Column(Integer, default=1)
    is_active = Column(Boolean, default=False)  # 标记是否为当前激活预设

    # 存储整个 root 节点树结构
    config_json = Column(Text, nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class DBLLMConfig(Base):
    """
    [新增] LLM API 配置表
    """
    __tablename__ = "llm_configs"

    id = Column(String, primary_key=True, index=True)
    name = Column(String, nullable=False)
    base_url = Column(String, nullable=False)
    api_key = Column(String, nullable=False)
    stream = Column(Boolean, default=True)
    default_model = Column(String, nullable=True)

    is_active = Column(Boolean, default=False)  # 标记是否为当前激活配置

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)