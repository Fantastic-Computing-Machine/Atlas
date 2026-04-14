"""ActionRun model — tracks label/archive/read actions."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class ActionRun(Base):
    """A batch action execution (e.g. applying labels)."""

    __tablename__ = "action_runs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    action_type: Mapped[str] = mapped_column(
        String(50), nullable=False, comment="apply_label | remove_label | archive | mark_read"
    )
    target_refs: Mapped[list[str] | None] = mapped_column(
        ARRAY(String), nullable=True, comment="Gmail message IDs targeted"
    )
    label_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("labels.id", ondelete="SET NULL"), nullable=True
    )
    preview_only: Mapped[bool] = mapped_column(Boolean, default=True)
    status: Mapped[str] = mapped_column(
        String(30), default="pending", comment="pending | previewing | applying | completed | failed"
    )
    result_count: Mapped[int | None] = mapped_column(comment="Number of messages affected")
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    def __repr__(self) -> str:
        return f"<ActionRun {self.action_type} status={self.status}>"
