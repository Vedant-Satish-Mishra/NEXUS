"""
NEXUS Database Models (SQLAlchemy 2 Async)
Covers all 13 core entities from Guide Section 0.5 with UUID primary keys,
timezone-aware timestamps, indexes, foreign key cascades, and unique constraints.
"""

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    MetaData,
    String,
    Text,
    UniqueConstraint,
    JSON,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

# Naming convention for stable Alembic migrations
NAMING_CONVENTION = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}

metadata_obj = MetaData(naming_convention=NAMING_CONVENTION)


def get_utc_now() -> datetime:
    return datetime.now(timezone.utc)


def generate_uuid() -> str:
    return str(uuid.uuid4())


class Base(DeclarativeBase):
    metadata = metadata_obj


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=get_utc_now, nullable=False)

    conversations: Mapped[List["Conversation"]] = relationship(
        "Conversation", back_populates="user", cascade="all, delete-orphan"
    )
    runs: Mapped[List["Run"]] = relationship("Run", back_populates="user", cascade="all, delete-orphan")
    files: Mapped[List["FileRecord"]] = relationship("FileRecord", back_populates="user", cascade="all, delete-orphan")
    memories: Mapped[List["Memory"]] = relationship("Memory", back_populates="user", cascade="all, delete-orphan")


class Conversation(Base):
    __tablename__ = "conversations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    title: Mapped[str] = mapped_column(String(255), default="New chat", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=get_utc_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=get_utc_now, onupdate=get_utc_now, nullable=False)

    user: Mapped["User"] = relationship("User", back_populates="conversations")
    agent_config: Mapped[Optional["ChatAgentConfig"]] = relationship(
        "ChatAgentConfig", back_populates="conversation", uselist=False, cascade="all, delete-orphan"
    )
    messages: Mapped[List["Message"]] = relationship("Message", back_populates="conversation", cascade="all, delete-orphan")
    runs: Mapped[List["Run"]] = relationship("Run", back_populates="conversation", cascade="all, delete-orphan")


class ChatAgentConfig(Base):
    __tablename__ = "chat_agent_configs"

    conversation_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("conversations.id", ondelete="CASCADE"), primary_key=True
    )
    preset: Mapped[str] = mapped_column(String(32), default="balanced", nullable=False)
    enabled_agents: Mapped[Any] = mapped_column(
        JSON().with_variant(JSONB, "postgresql"),
        default=lambda: ["controller", "retrieval", "reasoning", "memory", "evaluation"],
        nullable=False
    )
    auto_approve_plans: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    model_profile: Mapped[str] = mapped_column(String(32), default="fast", nullable=False)

    conversation: Mapped["Conversation"] = relationship("Conversation", back_populates="agent_config")


class Message(Base):
    __tablename__ = "messages"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    conversation_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("conversations.id", ondelete="CASCADE"), index=True, nullable=False
    )
    role: Mapped[str] = mapped_column(String(32), nullable=False)  # user, assistant, system
    content: Mapped[str] = mapped_column(Text, nullable=False)
    meta: Mapped[Optional[Any]] = mapped_column(JSON().with_variant(JSONB, "postgresql"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=get_utc_now, nullable=False)

    conversation: Mapped["Conversation"] = relationship("Conversation", back_populates="messages")
    feedbacks: Mapped[List["Feedback"]] = relationship("Feedback", back_populates="message", cascade="all, delete-orphan")


class Run(Base):
    __tablename__ = "runs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    conversation_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("conversations.id", ondelete="CASCADE"), index=True, nullable=False
    )
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    status: Mapped[str] = mapped_column(String(64), default="queued", index=True, nullable=False)
    tier: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    understanding: Mapped[Optional[Any]] = mapped_column(JSON().with_variant(JSONB, "postgresql"), nullable=True)
    plan: Mapped[Optional[Any]] = mapped_column(JSON().with_variant(JSONB, "postgresql"), nullable=True)
    evaluation: Mapped[Optional[Any]] = mapped_column(JSON().with_variant(JSONB, "postgresql"), nullable=True)
    retries: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    latency_ms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=get_utc_now, nullable=False)

    user: Mapped["User"] = relationship("User", back_populates="runs")
    conversation: Mapped["Conversation"] = relationship("Conversation", back_populates="runs")
    events: Mapped[List["RunEvent"]] = relationship("RunEvent", back_populates="run", cascade="all, delete-orphan")
    tool_executions: Mapped[List["ToolExecution"]] = relationship(
        "ToolExecution", back_populates="run", cascade="all, delete-orphan"
    )


class RunEvent(Base):
    __tablename__ = "run_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    run_id: Mapped[str] = mapped_column(String(36), ForeignKey("runs.id", ondelete="CASCADE"), index=True, nullable=False)
    seq: Mapped[int] = mapped_column(Integer, nullable=False)
    type: Mapped[str] = mapped_column(String(64), nullable=False)
    payload: Mapped[Any] = mapped_column(JSON().with_variant(JSONB, "postgresql"), nullable=False)

    run: Mapped["Run"] = relationship("Run", back_populates="events")

    __table_args__ = (
        UniqueConstraint("run_id", "seq", name="uq_run_events_run_id_seq"),
    )


class FileRecord(Base):
    __tablename__ = "files"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    conversation_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("conversations.id", ondelete="SET NULL"), nullable=True
    )
    scope: Mapped[str] = mapped_column(String(32), default="chat", nullable=False)  # chat, personal, system
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    mime: Mapped[str] = mapped_column(String(128), nullable=False)
    size: Mapped[int] = mapped_column(Integer, nullable=False)
    sha256: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="uploaded", index=True, nullable=False)
    error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    pages: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    chunks: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=get_utc_now, nullable=False)

    user: Mapped["User"] = relationship("User", back_populates="files")


class MemoryProposalRecord(Base):
    __tablename__ = "memory_proposals"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    run_id: Mapped[str] = mapped_column(String(36), ForeignKey("runs.id", ondelete="CASCADE"), index=True, nullable=False)
    kind: Mapped[str] = mapped_column(String(32), default="long_term", nullable=False)  # long_term, episodic
    content: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="pending", index=True, nullable=False)  # pending, accepted, edited, rejected
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=get_utc_now, nullable=False)


class Memory(Base):
    __tablename__ = "memories"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    kind: Mapped[str] = mapped_column(String(32), default="long_term", nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    source_run_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    confirmed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=get_utc_now, nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    chroma_id: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)

    user: Mapped["User"] = relationship("User", back_populates="memories")


class ToolExecution(Base):
    __tablename__ = "tool_executions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    run_id: Mapped[str] = mapped_column(String(36), ForeignKey("runs.id", ondelete="CASCADE"), index=True, nullable=False)
    tool: Mapped[str] = mapped_column(String(64), nullable=False)
    input: Mapped[str] = mapped_column(Text, nullable=False)
    output: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="completed", nullable=False)
    approved_by_user: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    duration_ms: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=get_utc_now, nullable=False)

    run: Mapped["Run"] = relationship("Run", back_populates="tool_executions")


class Feedback(Base):
    __tablename__ = "feedback"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    message_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("messages.id", ondelete="CASCADE"), index=True, nullable=False
    )
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    rating: Mapped[int] = mapped_column(Integer, nullable=False)  # +1 or -1
    comment: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=get_utc_now, nullable=False)

    message: Mapped["Message"] = relationship("Message", back_populates="feedbacks")

    __table_args__ = (
        UniqueConstraint("message_id", "user_id", name="uq_feedback_message_user"),
    )


class LearningSignal(Base):
    __tablename__ = "learning_signals"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    intent: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    strategy_key: Mapped[str] = mapped_column(String(128), index=True, nullable=False)
    signal: Mapped[str] = mapped_column(String(64), nullable=False)
    value: Mapped[float] = mapped_column(Float, nullable=False)
    source: Mapped[str] = mapped_column(String(32), nullable=False)  # feedback, evaluation, outcome
    run_id: Mapped[str] = mapped_column(String(36), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=get_utc_now, nullable=False)


class UserSettings(Base):
    __tablename__ = "user_settings"

    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    settings: Mapped[Any] = mapped_column(
        JSON().with_variant(JSONB, "postgresql"),
        default=lambda: {
            "model_profile": "fast",
            "default_preset": "balanced",
            "memory_enabled": True,
            "learning_enabled": True,
            "theme": "dark"
        },
        nullable=False
    )
