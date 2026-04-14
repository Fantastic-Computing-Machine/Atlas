"""User model."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class User(Base):
    """A connected Gmail user."""

    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    email: Mapped[str] = mapped_column(String(320), unique=True, nullable=False, index=True)
    auth_provider: Mapped[str] = mapped_column(String(50), default="google")
    encrypted_token_ref: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    mailbox_connection: Mapped[MailboxConnection | None] = relationship(
        "MailboxConnection", back_populates="user", uselist=False, cascade="all, delete-orphan"
    )
    scopes: Mapped[list[Scope]] = relationship(
        "Scope", back_populates="user", cascade="all, delete-orphan"
    )
    labels: Mapped[list[Label]] = relationship(
        "Label", back_populates="user", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<User {self.email}>"


# Avoid circular imports — these are resolved at runtime by SQLAlchemy string refs.
from app.models.mailbox import MailboxConnection  # noqa: E402, F811
from app.models.scope import Scope  # noqa: E402, F811
from app.models.label import Label  # noqa: E402, F811
