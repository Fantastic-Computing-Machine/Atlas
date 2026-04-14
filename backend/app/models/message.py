"""Message, Thread, and Extraction models."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, Float, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Message(Base):
    """A synced Gmail message (metadata + optional body reference)."""

    __tablename__ = "messages"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    gmail_message_id: Mapped[str] = mapped_column(
        String(100), nullable=False, index=True, unique=True
    )
    thread_id: Mapped[str | None] = mapped_column(String(100), index=True)
    internal_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    from_header: Mapped[str | None] = mapped_column(String(500))
    to_header: Mapped[str | None] = mapped_column(Text)
    subject: Mapped[str | None] = mapped_column(Text)
    snippet: Mapped[str | None] = mapped_column(Text)
    label_ids: Mapped[list[str] | None] = mapped_column(ARRAY(String))
    body_ref: Mapped[str | None] = mapped_column(
        Text, nullable=True, comment="Stored body text or reference"
    )
    raw_size: Mapped[int | None] = mapped_column(comment="Size estimate in bytes")
    is_read: Mapped[bool | None] = mapped_column(default=None)
    has_attachments: Mapped[bool | None] = mapped_column(default=None)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    # Relationships
    extraction: Mapped[Extraction | None] = relationship(
        "Extraction", back_populates="message", uselist=False, cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Message {self.gmail_message_id} subj={self.subject!r:.40}>"


class Thread(Base):
    """A canonical Gmail thread."""

    __tablename__ = "threads"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    gmail_thread_id: Mapped[str] = mapped_column(
        String(100), nullable=False, index=True, unique=True
    )
    subject_canonical: Mapped[str | None] = mapped_column(Text)
    participants: Mapped[list[str] | None] = mapped_column(ARRAY(String))
    first_message_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_message_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    message_count: Mapped[int | None] = mapped_column(default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    def __repr__(self) -> str:
        return f"<Thread {self.gmail_thread_id}>"


class Extraction(Base):
    """AI-extracted structured data from a message."""

    __tablename__ = "extractions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    message_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("messages.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    classifier_outputs: Mapped[dict | None] = mapped_column(
        JSONB, nullable=True, comment="Classification results as JSON"
    )
    entities_json: Mapped[dict | None] = mapped_column(
        JSONB, nullable=True, comment="Extracted entities"
    )
    dates_json: Mapped[dict | None] = mapped_column(
        JSONB, nullable=True, comment="Extracted dates/deadlines"
    )
    confidence: Mapped[float | None] = mapped_column(Float)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    # Relationships
    message: Mapped[Message] = relationship("Message", back_populates="extraction")

    def __repr__(self) -> str:
        return f"<Extraction msg={self.message_id} conf={self.confidence}>"
