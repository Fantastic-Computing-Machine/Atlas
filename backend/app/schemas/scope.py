"""Scope-related Pydantic schemas."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class ScopeCreate(BaseModel):
    """Request body for creating a scope."""

    name: str = Field(..., min_length=1, max_length=200)
    include_system_labels: list[str] | None = Field(
        default=None,
        description="System labels to include (e.g. INBOX, CATEGORY_PERSONAL)",
    )
    exclude_system_labels: list[str] | None = Field(
        default=None,
        description="System labels to exclude (e.g. CATEGORY_PROMOTIONS)",
    )
    include_user_labels: list[str] | None = None
    exclude_user_labels: list[str] | None = None
    default_date_window: int = Field(
        default=180,
        ge=1,
        le=3650,
        description="Lookback window in days",
    )


class ScopeUpdate(BaseModel):
    """Request body for updating a scope."""

    name: str | None = Field(default=None, min_length=1, max_length=200)
    include_system_labels: list[str] | None = None
    exclude_system_labels: list[str] | None = None
    include_user_labels: list[str] | None = None
    exclude_user_labels: list[str] | None = None
    default_date_window: int | None = Field(default=None, ge=1, le=3650)


class ScopeResponse(BaseModel):
    """Public scope representation."""

    id: uuid.UUID
    name: str
    include_system_labels: list[str] | None
    exclude_system_labels: list[str] | None
    include_user_labels: list[str] | None
    exclude_user_labels: list[str] | None
    default_date_window: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ScopePreview(BaseModel):
    """Preview of messages matching a scope."""

    scope_id: uuid.UUID
    scope_name: str
    gmail_query: str
    estimated_count: int | None = None
    sample_subjects: list[str] = []
