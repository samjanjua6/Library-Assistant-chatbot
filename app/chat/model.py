from __future__ import annotations

from datetime import datetime, timezone

# pyrefly: ignore [missing-import]
from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, BigInteger
# pyrefly: ignore [missing-import]
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..core.database import Base


class ChatSession(Base):
    __tablename__ = "chat_sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    title: Mapped[str] = mapped_column(String(255), default="New Chat", nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc), nullable=False
    )
    ended_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    last_message_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc), nullable=False
    )
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)
    # Optional relationship if needed
    # messages = relationship("ChatMessage", back_populates="session", cascade="all, delete-orphan")


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    session_id: Mapped[int] = mapped_column(ForeignKey("chat_sessions.id", ondelete="CASCADE"), index=True, nullable=False)
    role: Mapped[str] = mapped_column(String(50), nullable=False)  # "user" or "model"
    content: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc), nullable=False
    )


class SessionDocument(Base):
    """Tracks a file uploaded into a specific chat session.

    Status lifecycle:  pending → processing → ready
                                           └→ failed
    """
    __tablename__ = "session_documents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    session_id: Mapped[int] = mapped_column(
        ForeignKey("chat_sessions.id", ondelete="CASCADE"), index=True, nullable=False
    )
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )

    # File metadata
    original_filename: Mapped[str] = mapped_column(String(512), nullable=False)
    stored_filename: Mapped[str] = mapped_column(String(512), nullable=False)  # sanitised on-disk name
    file_size_bytes: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)
    mime_type: Mapped[str] = mapped_column(String(128), nullable=False, default="")

    # Processing status
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="pending"
    )  # pending | processing | ready | failed
    chunk_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
