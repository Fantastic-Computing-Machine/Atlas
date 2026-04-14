"""Label and LabelPolicy models."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, Float, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Label(Base):
    """A user-defined label (maps to a Gmail label)."""

    __tablename__ = "labels"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    gmail_label_id: Mapped[str | None] = mapped_column(
        String(200), nullable=True, comment="Gmail label ID after creation"
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    color: Mapped[str | None] = mapped_column(
        String(20), nullable=True, comment="Hex color for UI display"
    )
    status: Mapped[str] = mapped_column(
        String(30), default="active", comment="active | paused | archived"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    user: Mapped[User] = relationship("User", back_populates="labels")
    policy: Mapped[LabelPolicy | None] = relationship(
        "LabelPolicy", back_populates="label", uselist=False, cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Label {self.name}>"


class LabelPolicy(Base):
    """Classification policy attached to a Label."""

    __tablename__ = "label_policies"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    label_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("labels.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    description: Mapped[str | None] = mapped_column(
        Text, nullable=True, comment="Plain-English meaning of the label"
    )
    inclusions: Mapped[str | None] = mapped_column(
        Text, nullable=True, comment="What to include — free text"
    )
    exclusions: Mapped[str | None] = mapped_column(
        Text, nullable=True, comment="What to exclude — free text"
    )
    confidence_threshold: Mapped[float] = mapped_column(Float, default=0.85)
    apply_mode: Mapped[str] = mapped_column(
        String(30), default="label_only", comment="label_only | archive | mark_read"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    label: Mapped[Label] = relationship("Label", back_populates="policy")

    def __repr__(self) -> str:
        return f"<LabelPolicy label={self.label_id} threshold={self.confidence_threshold}>"


from app.models.user import User  # noqa: E402, F811
