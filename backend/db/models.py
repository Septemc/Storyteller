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
    Enum as SQLEnum,
)
from sqlalchemy.orm import relationship
from .base import Base
import enum
import uuid


class UserRole(enum.Enum):
    ADMIN = "admin"
    USER = "user"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, unique=True, index=True, nullable=False, default=lambda: f"{uuid.uuid4().hex[:12]}")
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(SQLEnum(UserRole), default=UserRole.USER, nullable=False)
    nickname = Column(String(50), nullable=True)
    avatar = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True)
    last_login_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    relationships = relationship("UserRelationship", back_populates="user", foreign_keys="UserRelationship.user_id")


class UserRelationship(Base):
    __tablename__ = "user_relationships"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(32), ForeignKey("users.user_id"), nullable=True, index=True)
    related_user_id = Column(String(32), ForeignKey("users.user_id"), nullable=True, index=True)
    relationship_type = Column(String(20), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="relationships", foreign_keys=[user_id])


class WorldbookEntry(Base):
    __tablename__ = "worldbook"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(32), ForeignKey("users.user_id"), nullable=True, index=True)
    entry_id = Column(String, unique=True, index=True, nullable=False)
    category = Column(String, index=True, nullable=True)
    tags = Column(String, nullable=True)
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

    id = Column(String, primary_key=True, index=True)
    user_id = Column(String(32), ForeignKey("users.user_id"), nullable=True, index=True)
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    config_json = Column(Text, nullable=False, default="{}")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Character(Base):
    __tablename__ = "characters"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(32), ForeignKey("users.user_id"), nullable=True, index=True)
    character_id = Column(String, unique=True, index=True, nullable=False)
    template_id = Column(String, default="system_default", nullable=True)
    type = Column(String, nullable=False, default="npc")
    data_json = Column(Text, nullable=True)
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
    user_id = Column(String(32), ForeignKey("users.user_id"), nullable=True, index=True)
    key = Column(String, unique=True, nullable=False)
    value_json = Column(Text, nullable=False)


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
    """
    [新增] 脚本/剧本主表
    存储脚本的元数据和概览信息
    """
    __tablename__ = "scripts"

    id = Column(Integer, primary_key=True, index=True)
    script_id = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    
    # 脚本中包含的所有副本ID列表 (JSON存储，格式: ["dungeon_id_1", "dungeon_id_2"])
    dungeon_ids_json = Column(Text, nullable=True, default="[]")
    
    # 元数据
    meta_json = Column(Text, nullable=True)  # 额外的tag、category等
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class SessionState(Base):
    __tablename__ = "session_state"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(32), ForeignKey("users.user_id"), nullable=True, index=True)
    session_id = Column(String, unique=True, index=True, nullable=False)
    
    # 当前应用的脚本
    current_script_id = Column(String, nullable=True)
    
    # 当前选中的副本和节点
    current_dungeon_id = Column(String, nullable=True)
    current_node_id = Column(String, nullable=True)
    
    # 其他字段
    player_position_json = Column(Text, nullable=True)
    global_state_json = Column(Text, nullable=True)
    total_word_count = Column(Integer, default=0)
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )


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
    """
    [RAG] 世界书向量缓存表
    存储世界书条目的向量化表示，用于语义检索
    """
    __tablename__ = "worldbook_embeddings"

    id = Column(Integer, primary_key=True, index=True)
    entry_id = Column(String, ForeignKey("worldbook_entries.entry_id"), nullable=False, index=True)
    
    # 向量数据 (SQLite 使用 JSON 存储数组)
    embedding_json = Column(Text, nullable=False)  # 存储为 JSON 数组字符串
    
    # 元数据
    content_hash = Column(String, nullable=False, index=True)  # 用于检测内容变更
    embedding_model = Column(String, nullable=False)  # 使用的模型标识
    dimension = Column(Integer, nullable=False)  # 向量维度
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)