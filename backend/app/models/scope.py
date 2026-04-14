"""Scope model — defines what Atlas can search."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Scope(Base):
    """A saved scope object defining which mailbox segments Atlas can search."""

    __tablename__ = "scopes"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    include_system_labels: Mapped[list[str] | None] = mapped_column(
        ARRAY(String), nullable=True, comment="e.g. INBOX, CATEGORY_PERSONAL"
    )
    exclude_system_labels: Mapped[list[str] | None] = mapped_column(
        ARRAY(String), nullable=True, comment="e.g. CATEGORY_PROMOTIONS"
    )
    include_user_labels: Mapped[list[str] | None] = mapped_column(
        ARRAY(String), nullable=True, comment="User-created Gmail label IDs"
    )
    exclude_user_labels: Mapped[list[str] | None] = mapped_column(
        ARRAY(String), nullable=True
    )
    default_date_window: Mapped[int] = mapped_column(
        Integer, default=180, comment="Default lookback window in days"
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
    user: Mapped[User] = relationship("User", back_populates="scopes")

    def __repr__(self) -> str:
        return f"<Scope {self.name}>"


from app.models.user import User  # noqa: E402, F811
