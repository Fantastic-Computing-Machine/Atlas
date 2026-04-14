"""QueryRun model — tracks natural-language query executions."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class QueryRun(Base):
    """A single natural-language query execution and its results."""

    __tablename__ = "query_runs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    raw_question: Mapped[str] = mapped_column(Text, nullable=False)
    structured_plan_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    scope_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("scopes.id", ondelete="SET NULL"), nullable=True
    )
    status: Mapped[str] = mapped_column(
        String(30), default="pending", comment="pending | running | completed | failed"
    )
    answer_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    evidence_refs: Mapped[list[str] | None] = mapped_column(
        ARRAY(String), nullable=True, comment="Message/thread IDs used as evidence"
    )
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    def __repr__(self) -> str:
        return f"<QueryRun {self.id} status={self.status}>"
